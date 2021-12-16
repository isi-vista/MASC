"""Analysis of sentence similarity model event primitive prediction."""
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, List, Mapping, Sequence, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sn
from sklearn.metrics import confusion_matrix

from pycurator.flask_backend.event_prediction import init_embeddings, init_ss_model, request_top_n


@dataclass
class SchemaAnalysisObj:
    """Store information about the schema for easy write out to CSV.

    Attributes:
        text: Text corresponding to the event step.
        true_event_primitive: Event primitive assigned to this event step by annotator.
        pred_event_primitives: Event primitives predicted by the sentence similarity model, listed
            in order of most likely -> least likely.
    """

    text: str
    true_event_primitive: str
    pred_event_primitives: Sequence[str]

    def __iter__(self) -> Iterable[str]:
        """Represent the obj as an iterable."""
        return iter([self.text, self.true_event_primitive, *self.pred_event_primitives])


def main(args: Namespace) -> None:
    """Read in schemas, score for accuracy and MRR, write out results, and plot (optional).

    Arguments:
        args: Arguments read in from the command line.
    """
    schema_path = args.input
    schemas = read_in_schemas(schema_path)

    ss_model = init_ss_model()
    definition_emb, template_emb = init_embeddings(ss_model)

    annotated_schemas = []

    for schema in schemas:
        for step in schema["steps"]:
            description = step["name"].replace(",", ";").replace("-", " ")
            top_5: List[str] = []
            for pred in request_top_n(
                description,
                n=5,
                ss_model=ss_model,
                definition_embeddings=definition_emb,
                template_embeddings=template_emb,
            ):
                pred_type = cast(str, pred["type"])
                top_5.append(pred_type)
            s = SchemaAnalysisObj(
                description,
                ".".join(step["@type"].split("/")[-1].split(".")[:2]),
                top_5,
            )
            annotated_schemas.append(s)

    path_to_schema_events = Path("all_schema_events.csv")
    # Checkpoint in case we want to do anything else with this information
    schemas_df = write_out_scores(annotated_schemas, path_to_schema_events)

    output_path = args.output
    analyze_results(output_path, schemas_df)

    if args.plot:
        plot(schemas_df)


def plot(results: pd.DataFrame) -> None:
    """Create confusion matrix from results of the analysis.

    Arguments:
        results: Results from events and predictions.
    """
    labels = results.true_primitive.unique().tolist()
    cm = confusion_matrix(
        results.true_primitive.tolist(),
        results.rec_primitive_1.tolist(),
        labels=labels,
        normalize="true",
    )
    plt.figure(figsize=(15, 15))
    sn.heatmap(cm, cmap="YlGnBu", xticklabels=labels, yticklabels=labels)
    plt.savefig("confusion_matrix.pdf", bbox_inches="tight", dpi=500)


def write_out_scores(
    annotated_schemas: Sequence[SchemaAnalysisObj], path_to_schema_events: Path
) -> pd.DataFrame:
    """Write out results from predicting event types for each step.

    Arguments:
        annotated_schemas: List of SchemaAnalysisObj's containing all the important
            information from the schemas and predictions over event types.
        path_to_schema_events: Path to the schema events file.

    Returns:
        DataFrame containing matching event text, true event primitive, and top five recommended
            primitives.
    """
    df = pd.DataFrame.from_records(
        annotated_schemas,
        columns=[
            "event_text",
            "true_primitive",
            "rec_primitive_1",
            "rec_primitive_2",
            "rec_primitive_3",
            "rec_primitive_4",
            "rec_primitive_5",
        ],
    )
    df.to_csv(path_to_schema_events)
    return df


def mean_reciprocal_rank(rs: Sequence[Sequence[int]]) -> np.float64:
    """Calculate MRR (from https://gist.github.com/bwhite/3726239).

    Arguments:
        rs: Matches for each event primitive type.

    Returns:
        Calculated MRR.
    """
    rs_gen = (np.asarray(r).nonzero()[0] for r in rs)
    return cast(np.float64, np.mean([1.0 / (r[0] + 1) if r.size else 0.0 for r in rs_gen]))


def analyze_results(output_path: Path, results: pd.DataFrame) -> None:
    """Analyze results of the event primitive prediction over schemas.

    Specifically, calculate how many matches there are between the true event primitive and
    predictive event primitives. Then get the mean reciprocal rank, and the accuracy for
    predictions at the first prediction, top three predictions, and top five predictions.

    Arguments:
        output_path: Path to the output file.
        results: Pandas DataFrame containing event text, true primitive, predicted primitives.
    """
    temp_df = pd.DataFrame()
    temp_df["first_match"] = np.where(results.true_primitive == results.rec_primitive_1, 1, 0)
    temp_df["second_match"] = np.where(results.true_primitive == results.rec_primitive_2, 1, 0)
    temp_df["third_match"] = np.where(results.true_primitive == results.rec_primitive_3, 1, 0)

    mrr = mean_reciprocal_rank(temp_df.values.tolist())

    results["first_match"] = temp_df.first_match
    results["top_three"] = np.where(
        results.first_match
        | (results.true_primitive == results.rec_primitive_2)
        | (results.true_primitive == results.rec_primitive_3),
        1,
        0,
    )
    results["top_five"] = np.where(
        results.top_three
        | (results.true_primitive == results.rec_primitive_4)
        | (results.true_primitive == results.rec_primitive_5),
        1,
        0,
    )
    results["no_match"] = np.where(results.top_five == 0, 1, 0)

    top1_accuracy = np.sum(results.first_match) / len(results.first_match)
    top3_accuracy = np.sum(results.top_three) / len(results.top_three)
    top5_accuracy = np.sum(results.top_five) / len(results.top_five)

    print(f"Accuracy@Top1: {top1_accuracy}")
    print(f"Accuracy@Top3: {top3_accuracy}")
    print(f"Accuracy@Top5: {top5_accuracy}")

    print(f"MRR: {mrr}")
    results.to_csv(output_path)


def read_in_schemas(schema_path: Path) -> Sequence[Mapping[str, Any]]:
    """Read in schema information from *schema_path*.

    Arguments:
        schema_path: Path to the schemas as SDF.

    Returns:
        List of schemas.
    """
    with open(schema_path) as handle:
        response: Sequence[Mapping[str, Any]] = json.load(handle)["schemas"]
        return response


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--input",
        help="Path to JSON file containing all available schemas in SDF format.",
        type=Path,
    )
    parser.add_argument(
        "--output",
        help="""Path to output CSV file containing schema steps with correct and predicted event
        primitives.""",
        type=Path,
        default="schema_events_with_counts.csv",
    )
    parser.add_argument("--plot", "-p", action="store_true", help="Generate confusion matrix.")

    arguments = parser.parse_args()
    main(arguments)
