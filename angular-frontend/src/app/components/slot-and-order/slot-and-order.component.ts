import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { ClusterNode, Edge, Node } from '@swimlane/ngx-graph';
import { ToastrService } from 'ngx-toastr';
import { Subject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Event } from '../../models/Event';
import { Primitive } from '../../models/Primitive';

export interface SubmissionResponse {
  fname: string;
  output: string;
}

export interface QnodeOption {
  qnode: string;
  rawName: string;
  definition: string;
}

export interface QnodeSelector {
  query: string;
  options: QnodeOption[];
  qnode: string;
  selectedQnode: string;
}

export interface QnodeResponse {
  query: string;
  options: QnodeOption[];
}

@Component({
  selector: 'app-slot-and-order',
  templateUrl: './slot-and-order.component.html',
  styleUrls: ['./slot-and-order.component.css'],
})
export class SlotAndOrderComponent implements OnInit {
  @ViewChild('name_popup') name_popup: ElementRef;
  @ViewChild('c_arg_popup') c_a_popup: ElementRef;

  // Variables for multiselect actions
  mselect_order: string;
  anchor_id_num: string; // TODO: Should be number, but needs to be parsed somehow

  // Variables for graphing
  nodes: Node[];
  links: Edge[];
  clusters: ClusterNode[]; // Object to cluster nodes together. Not used as of yet.
  center$: Subject<boolean> = new Subject(); // Graph subject to trigger centering
  zoomToFit$: Subject<boolean> = new Subject(); // Graph subject to fit graph to window
  update$: Subject<boolean> = new Subject();

  // Graph modifiers, bound to the input fields
  source_idx: number;
  dest_idx: number;

  refvar_name: string;
  constraints: string[];

  download_flag = false;
  reset_flag = true;

  schema_id: string;
  schema_name: string;
  schema_dscpt: string;
  rec_events: string[][];
  tracking: { date: string; type: string; data: unknown }[];

  events: Event[];
  primitives: Primitive[];
  node_ct: number;
  eventSelectors: QnodeSelector[] = [];
  eventSelectorMap: Map<string, QnodeSelector> = new Map();
  refvarSelectors: QnodeSelector[] = [];
  refvarSelectorMap: Map<string, QnodeSelector> = new Map();

  showCommonArgs = false;

  schema_output: SubmissionResponse;
  private apiUrl = environment.API_URL;

  constructor(
    private http: HttpClient,
    private router: Router,
    private toastr: ToastrService,
    public dialog: MatDialog
  ) {
    this.schema_output = null;
    if (history.state.data === undefined) {
      alert('Enter events first'); // eslint-disable-line no-alert
      this.router.navigate(['/']);
    } else {
      this.events = history.state.data.events;
      this.node_ct = history.state.data.node_ct;
    }

    this.nodes = history.state.data.nodes;
    this.links = history.state.data.links;
    this.clusters = history.state.data.clusters;
    this.schema_id = history.state.data.schema_id;
    this.schema_name = history.state.data.schema_name;
    this.schema_dscpt = history.state.data.schema_dscpt;
    this.eventSelectors = history.state.data.eventSelectors;
    this.eventSelectorMap = history.state.data.eventSelectorMap;
    this.refvarSelectors = history.state.data.refvarSelectors;
    this.refvarSelectorMap = history.state.data.refvarSelectorMap;
    this.primitives = history.state.data.primitives;
    this.rec_events = history.state.data.rec_events;
    this.tracking = history.state.data.tracking;

    const refvars: string[] = [];
    for (const event of this.events) {
      if (event.args) {
        for (const arg of event.args) {
          if (!refvars.includes(arg.refvar)) {
            refvars.push(arg.refvar);
          }
        }
      }
    }
    for (const refvar of refvars) {
      this.getDisambigResponse(refvar);
    }
  }

  ngOnInit(): void {
    this.refreshGraph();

    // If no event suggestions, take up the whole left screen for event table
    const tableBody = document.getElementById('slotting-table-body');
    if (this.rec_events.length < 1) {
      tableBody.className = 'slotting-table-body-lg';
    }
  }

  getDisambigResponse(refvar: string): void {
    if (this.refvarSelectorMap.has(refvar)) {
      const selector = this.refvarSelectorMap.get(refvar);
      if (selector.options.length > 0) {
        return;
      }
    }
    const url = this.apiUrl + '/api/disambiguate_refvar_kgtk';
    this.http
      .post(url, { refvar })
      .toPromise()
      .then((data: QnodeResponse) => {
        // Set mapping from qnode raw name to actual qnode id
        const options: QnodeOption[] = data.options;
        let selector: QnodeSelector = {
          query: refvar,
          options: [],
          qnode: '',
          selectedQnode: '',
        };
        if (this.refvarSelectorMap.has(refvar)) {
          selector = this.refvarSelectorMap.get(refvar);
        }
        if (options.length > 0) {
          const nullOption = {
            qnode: '',
            rawName: 'None of the above',
            definition: '',
          };
          options.push(nullOption);
          selector.options = options;
        }
        if (!selector.qnode || options.length === 0) {
          selector.qnode = '';
          selector.selectedQnode = '';
        }
        if (!this.refvarSelectorMap.has(refvar)) {
          this.refvarSelectors.push(selector);
        }
        this.refvarSelectorMap.set(refvar, selector);
      });
  }

  showCommonArgPopup(): void {
    const popup_native = this.c_a_popup.nativeElement;
    popup_native.style.display = 'block';
  }

  // Methods to modify the graph

  refreshGraph(): void {
    this.nodes = [...this.nodes];
    this.links = [...this.links];
  }

  addNode(link_bundle: { event: Event; addlink: boolean }): void {
    const event: Event = link_bundle.event;
    const addlink = link_bundle.addlink;
    const node: Node = {
      id: event.event_text,
      label: event.id,
    };
    this.nodes.push(node);

    let rec_idx = -1;
    let event_idx = -1;
    let found_rec = false;
    for (let i = 0; i < this.rec_events.length; i++) {
      for (let j = 1; j < this.rec_events[i].length; j++) {
        if (this.rec_events[i][j] === event.event_text) {
          rec_idx = i;
          event_idx = j;
          found_rec = true;
          break;
        }
      }
      if (found_rec) {
        break;
      }
    }
    if (addlink) {
      const rec_id_num = this.events
        .find((e) => e.event_text === this.rec_events[rec_idx][0])
        .id_num.toString();
      const link_id: string = 'E' + rec_id_num + '-E' + event.id_num.toString();
      const link: Edge = {
        id: link_id,
        source: this.rec_events[rec_idx][0],
        target: event.event_text,
        label: '',
      };
      this.links.push(link);
    }
    // Remove recommendation from rec_events
    this.rec_events[rec_idx].splice(event_idx, 1);

    if (this.rec_events[rec_idx].length === 1) {
      this.rec_events.splice(rec_idx, 1);
    }
    this.refreshGraph();
  }

  updateSchemaDetails(schemaDetails: {
    schema_id: string;
    schema_name: string;
    schema_dscpt: string;
  }): void {
    this.schema_id = schemaDetails.schema_id;
    this.schema_name = schemaDetails.schema_name;
    this.schema_dscpt = schemaDetails.schema_dscpt;
  }

  edgeExists(source: string, target: string): boolean {
    for (const link of this.links) {
      if (link.source === source && link.target === target) {
        return true;
      }
    }
    return false;
  }

  addEdges(): number {
    // Validating input/ checking for errors
    let flag = true;
    if (this.anchor_id_num === null || this.anchor_id_num === undefined) {
      this.toastr.error('No anchor event selected', '', { timeOut: 1500 });
      return 0;
    }
    if (this.mselect_order === null || this.mselect_order === undefined) {
      this.toastr.error('Event order not defined', '', { timeOut: 1500 });
      return 0;
    }
    for (const e of this.events) {
      if (e.is_checked === true) {
        flag = false;
      }
      if (e.is_checked && e.id_num === parseInt(this.anchor_id_num, 10)) {
        this.toastr.error(
          'cannot form edges from anchor to self. Please deselect the anchor and try again',
          '',
          { timeOut: 3000 }
        );
        return 0;
      }
    }

    if (flag) {
      this.toastr.error('No event selected', '', { timeOut: 1500 });
      return 0;
    }

    const anchor_idx = this.events.findIndex((e) => e.id_num === parseInt(this.anchor_id_num, 10));
    const anchor_e_text = this.events[anchor_idx].event_text;

    for (const e of this.events) {
      if (e.is_checked === true) {
        if (this.mselect_order === 'succeed' && this.edgeExists(anchor_e_text, e.event_text)) {
          this.toastr.error(
            "Edge between '" + anchor_e_text + "' and '" + e.event_text + "' already exists"
          );
          return 0;
        } else if (
          this.mselect_order === 'precede' &&
          this.edgeExists(e.event_text, anchor_e_text)
        ) {
          this.toastr.error(
            "Edge between '" + anchor_e_text + "' and '" + e.event_text + "' already exists"
          );
          return 0;
        }
      }
    }

    // Adding Edges
    const selected: string[] = [];
    for (const e of this.events) {
      if (e.is_checked === true) {
        selected.push(e.event_text);
      }
    }

    const anchor_id_num = this.events.find((e) => e.event_text === anchor_e_text).id_num.toString();
    if (this.mselect_order === 'precede') {
      for (const e_text of selected) {
        const e_id_num = this.events.find((e) => e.event_text === e_text).id_num.toString();
        const link_id: string = 'E' + e_id_num + '-E' + anchor_id_num;
        const link: Edge = {
          id: link_id,
          source: e_text,
          target: anchor_e_text,
          label: '',
        };
        this.links.push(link);
      }
    } else if (this.mselect_order === 'succeed') {
      for (const e_text of selected) {
        const e_id_num = this.events.find((e) => e.event_text === e_text).id_num.toString();
        const link_id: string = 'E' + anchor_id_num + '-E' + e_id_num;
        const link: Edge = {
          id: link_id,
          source: anchor_e_text,
          target: e_text,
          label: '',
        };
        this.links.push(link);
      }
    }

    this.refreshGraph();
    // Reset checkboxes and form
    for (const e of this.events) {
      e.is_checked = false;
    }
    this.mselect_order = null;
    this.anchor_id_num = null;
    return 0;
  }

  addEdge(): number {
    if (this.source_idx === this.dest_idx) {
      this.toastr.error('Cannot create edges to self');
      return 0;
    }
    if (
      this.edgeExists(
        this.events[this.source_idx].event_text,
        this.events[this.dest_idx].event_text
      )
    ) {
      this.toastr.error('Edge already exists');
      return 0;
    }
    const source_id_num = this.events[this.source_idx].id_num.toString();
    const dest_id_num = this.events[this.dest_idx].id_num.toString();
    const link_id: string = 'E' + source_id_num + '-E' + dest_id_num;
    const link: Edge = {
      id: link_id,
      source: this.events[this.source_idx].event_text,
      target: this.events[this.dest_idx].event_text,
      label: '',
    };
    this.links.push(link);
    this.source_idx = null;
    this.dest_idx = null;
    this.refreshGraph();
    return 0;
  }

  removeEdge(): void {
    const index = this.links.findIndex(
      (l) =>
        l.source === this.events[this.source_idx].event_text &&
        l.target === this.events[this.dest_idx].event_text
    );
    if (index === -1) {
      this.toastr.error('Edge does not exist');
    } else {
      this.links.splice(index, 1);
      this.refreshGraph();
    }
    this.source_idx = null;
    this.dest_idx = null;
  }

  onCLickBack(): void {
    const events = this.events;
    const nodes = this.nodes;
    const links = this.links;
    const clusters = this.clusters;
    const node_ct = this.node_ct;
    const schema_id = this.schema_id;
    const schema_name = this.schema_name;
    const schema_dscpt = this.schema_dscpt;
    const eventSelectors = this.eventSelectors;
    const eventSelectorMap = this.eventSelectorMap;
    const refvarSelectors = this.refvarSelectors;
    const refvarSelectorMap = this.refvarSelectorMap;
    const rec_events = this.rec_events;
    const tracking = this.tracking;
    this.router.navigate(['/'], {
      state: {
        data: {
          events,
          nodes,
          links,
          clusters,
          node_ct,
          eventSelectors,
          eventSelectorMap,
          refvarSelectors,
          refvarSelectorMap,
          schema_id,
          schema_name,
          schema_dscpt,
          rec_events,
          tracking,
        },
      },
    });
  }

  async postSchema(): Promise<number> {
    this.saveLinks();
    await this.http
      .post(this.apiUrl + '/api/save_schema', {
        events: this.events,
        links: this.links,
        schema_id: this.schema_id,
        schema_name: this.schema_name,
        schema_dscpt: this.schema_dscpt,
        tracking: this.tracking,
      })
      .toPromise()
      .then((data: SubmissionResponse) => {
        this.schema_output = data;
      })
      .catch((error: HttpErrorResponse) => {
        let message = 'Schema not submitted successfully. Check log for more information.';
        if (error.status === 400 && error.error.fname === 'err') {
          const error_msg = error.error.output;
          if (error_msg === 'cycle in graph') {
            message = 'Cycle detected in graph. Please remove cycle and try again.';
          } else if (error_msg === 'refvar constraints not consistent') {
            message =
              'Inconsistent refvar constraints. Please ensure all refvars of same string have consistent constraints.';
          }
        } else {
          console.error(error.message);
        }
        this.toastr.error(message);
        throw new Error('Schema not submitted successfully.');
      });

    this.toastr.success('Schema submitted successfully!');

    // Downloading the submitted YAML file
    if (this.download_flag) {
      const element = document.createElement('a');
      const fileType = 'text/plain';
      element.setAttribute(
        'href',
        `data:${fileType};charset=utf-8,${encodeURIComponent(this.schema_output.output)}`
      );
      element.setAttribute('download', this.schema_output.fname + '.yaml');
      const event = new MouseEvent('click');
      element.dispatchEvent(event);
    }

    if (this.reset_flag) {
      const events = [];
      const nodes = [];
      const links = [];
      const clusters = [];
      const node_ct = 0;
      const schema_id = undefined;
      const schema_name = undefined;
      const schema_dscpt = undefined;
      const eventSelectors = [];
      const eventSelectorMap = new Map();
      const refvarSelectorMap = new Map();
      const refvarSelectors = [];
      const rec_events = [];
      const tracking = [];
      this.router.navigate(['/'], {
        state: {
          data: {
            events,
            nodes,
            links,
            clusters,
            node_ct,
            eventSelectors,
            eventSelectorMap,
            refvarSelectorMap,
            refvarSelectors,
            schema_id,
            schema_name,
            schema_dscpt,
            rec_events,
            tracking,
          },
        },
      });
    }

    return 0;
  }

  // Schema Submission and Download
  submitSchema(): number {
    // Metadata verification
    if (
      this.schema_id === undefined ||
      this.schema_name === undefined ||
      this.schema_dscpt === undefined
    ) {
      this.toastr.error('Enter schema ID, name and description values to continue');
      return 0;
    }
    const regexp = new RegExp('^\\S+$');
    if (!regexp.test(this.schema_id)) {
      this.toastr.error('Invalid ID entered');
      return 0;
    }
    if (this.schema_dscpt === '' || this.schema_name === '') {
      this.toastr.error('Schema name/description cannot be empty');
      return 0;
    }

    this.postSchema();

    return 0;
  }

  checkForRecommendations(): boolean {
    return this.rec_events !== undefined && this.rec_events.length > 0;
  }

  rolesFilled(): boolean {
    for (const e of this.events) {
      if (e.is_checked && (e.staged_arg === null || e.staged_arg === undefined)) {
        return false;
      }
    }
    return true;
  }

  getCommonConstraints(): string[] {
    let common_constraints: string[] = [];

    const checked_events = this.events.filter((e) => e.is_checked);
    if (checked_events.length > 0) {
      common_constraints = checked_events[0].staged_constraints;
    }

    for (const eve of checked_events) {
      common_constraints = common_constraints.filter((c) => eve.staged_constraints.includes(c));
    }
    return common_constraints;
  }

  addArg(): number {
    // Refvar validation
    if (!this.refvar_name || !this.refvar_name.trim().length) {
      this.toastr.error('Empty strings are not allowed.');
      return 0;
    }
    this.refvar_name = this.refvar_name.trim();
    for (const event of this.events) {
      if (event.is_checked) {
        this.getDisambigResponse(this.refvar_name);
        if (event.args === null || event.args === undefined) {
          event.args = [
            { role: event.staged_arg, refvar: this.refvar_name, constraints: this.constraints },
          ];
        } else {
          event.args.push({
            role: event.staged_arg,
            refvar: this.refvar_name,
            constraints: this.constraints,
          });
        }
      }
    }
    return 0;
  }

  eventSelectedForArg(): void {
    let flag = false;
    for (const event of this.events) {
      if (event.is_checked) {
        flag = true;
      }
    }

    if (flag) {
      this.showCommonArgs = true;
    } else {
      this.toastr.error('No event selected.', '', { timeOut: 1500 });
      this.showCommonArgs = false;
    }
  }

  recenterGraph(): void {
    this.zoomToFit$.next(true);
    this.center$.next(true);
  }

  // Iterate through events, if event arg refvar matches selector update reference & comment;
  // Update selector.qnode == selector.selectedQnode to save selection.
  saveLinks(): void {
    for (const event of this.events) {
      if (this.eventSelectorMap.has(event.event_text)) {
        const selector = this.eventSelectorMap.get(event.event_text);
        let rawName;
        for (const option of selector.options) {
          if (option.qnode === selector.qnode) {
            rawName = option.rawName;
          }
        }
        if (selector.qnode) {
          event.reference = selector.qnode;
          event.comment = 'Qnode: ' + rawName;
        }
      }
      if (event.args === null || event.args === undefined) {
        continue;
      }
      for (const arg of event.args.filter((a) => a.refvar)) {
        if (this.refvarSelectorMap.has(arg.refvar)) {
          const selector = this.refvarSelectorMap.get(arg.refvar);
          let rawName;
          for (const option of selector.options) {
            if (option.qnode === selector.qnode) {
              rawName = option.rawName;
            }
          }
          if (selector.qnode) {
            arg.reference = selector.qnode;
            arg.comment = 'Qnode: ' + rawName;
          }
        }
      }
    }
  }

  // Underlying slot edited, check if refvar changed;
  // If so, disambiguate new refvar, check refvar still used.
  checkRefvar(event: [string, string]): void {
    let newRefvar;
    let oldRefvar;
    // If edited, both new and old refvar send in event
    if (event.length > 1) {
      newRefvar = event[0];
      oldRefvar = event[1];
      if (!this.refvarSelectorMap.has(newRefvar)) {
        this.getDisambigResponse(newRefvar);
      }
    } else {
      oldRefvar = event[0];
    }
    let used = false;
    for (const eve of this.events.filter((e) => e.args)) {
      for (const arg of eve.args.filter((a) => a.refvar)) {
        if (arg.refvar === oldRefvar) {
          used = true;
        }
      }
    }
    if (!used) {
      if (this.refvarSelectorMap.has(oldRefvar)) {
        const selector = this.refvarSelectorMap.get(oldRefvar);
        this.refvarSelectorMap.delete(oldRefvar);
        const index = this.refvarSelectors.indexOf(selector, 0);
        if (index > -1) {
          this.refvarSelectors.splice(index, 1);
        }
      }
    }
  }
}
