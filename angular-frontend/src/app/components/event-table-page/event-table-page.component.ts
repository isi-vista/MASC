import { HttpClient } from '@angular/common/http';
import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ClusterNode, Edge, Node } from '@swimlane/ngx-graph';
import { ToastrService } from 'ngx-toastr';
import { environment } from '../../../environments/environment';
import { Event } from '../../models/Event';
import { Primitive } from '../../models/Primitive';
import { RecommendationsResponse } from '../event-table/event-table.component';
import { SchemaFilesResponse } from '../load-schema/load-schema.component';
import {
  QnodeOption,
  QnodeResponse,
  QnodeSelector,
} from '../slot-and-order/slot-and-order.component';

@Component({
  selector: 'app-event-table-page',
  templateUrl: './event-table-page.component.html',
  styleUrls: ['./event-table-page.component.css'],
})
export class EventTablePageComponent {
  node_ct: number;
  events: Event[];

  // Variables for graphing
  nodes: Node[];
  links: Edge[];
  clusters: ClusterNode[]; // Object to cluster nodes together. Not used as of yet.

  // Schema loading variables
  response: RecommendationsResponse;
  savedSchemas: string[];
  schemaFile: string;
  schema_id: string;
  schema_name: string;
  schema_dscpt: string;
  schema_suggestion = 'linear';
  primitives: Primitive[];
  rec_events: string[][];
  eventSelectors: QnodeSelector[] = [];
  eventSelectorMap: Map<string, QnodeSelector> = new Map();
  refvarSelectors: QnodeSelector[] = [];
  refvarSelectorMap: Map<string, QnodeSelector> = new Map();
  tracking: { date: string; type: string; data: unknown }[];
  private apiUrl = environment.API_URL;

  // Event suggestion variables
  event_suggestion: boolean;
  section_clear = false;

  constructor(private http: HttpClient, private router: Router, private toastr: ToastrService) {
    // Listen for reloads and warn user when reloading page
    window.addEventListener('beforeunload', (event) => {
      // Most browsers might override this and present a generic message
      event.returnValue =
        'Are you sure you want to leave? All unsaved/unsubmitted data will be lost';
    });

    if (history.state.data === undefined) {
      this.events = [];
      this.nodes = [];
      this.links = [];
      this.clusters = [];
      this.node_ct = 0;
      this.rec_events = [];
      this.tracking = [];
    } else {
      this.events = history.state.data.events;
      this.nodes = history.state.data.nodes;
      this.links = history.state.data.links;
      this.clusters = history.state.data.clusters;
      this.node_ct = history.state.data.node_ct;
      this.schema_id = history.state.data.schema_id;
      this.schema_name = history.state.data.schema_name;
      this.schema_dscpt = history.state.data.schema_dscpt;
      this.eventSelectors = history.state.data.eventSelectors;
      this.eventSelectorMap = history.state.data.eventSelectorMap;
      this.refvarSelectors = history.state.data.refvarSelectors;
      this.refvarSelectorMap = history.state.data.refvarSelectorMap;
      this.rec_events = history.state.data.rec_events;
      this.tracking = history.state.data.tracking;
      if (this.events) {
        for (const event of this.events) {
          this.getEventQnodes(event.event_text);
        }
      }
    }
    this.event_suggestion = router.url === '/event-suggestion';
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

  async getSavedSchemas(): Promise<void> {
    return this.http
      .get(this.apiUrl + '/api/get_saved_schemas')
      .toPromise()
      .then((data: SchemaFilesResponse) => {
        this.savedSchemas = data.schemaFiles;
      });
  }

  getEventQnodes(event_description: string): void {
    if (this.eventSelectorMap.has(event_description)) {
      const selector = this.eventSelectorMap.get(event_description);
      if (selector.options.length > 0) {
        return;
      }
    }
    const url = this.apiUrl + '/api/disambiguate_verb_kgtk';
    this.http
      .post(url, { event_description })
      .toPromise()
      .then((data: QnodeResponse) => {
        // Set mapping from qnode raw name to actual qnode id
        const options: QnodeOption[] = data.options;
        let selector: QnodeSelector = {
          query: event_description,
          options: [],
          qnode: '',
          selectedQnode: '',
        };
        if (this.eventSelectorMap.has(event_description)) {
          selector = this.eventSelectorMap.get(event_description);
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
        if (!this.eventSelectorMap.has(event_description)) {
          this.eventSelectors.push(selector);
        }
        this.eventSelectorMap.set(event_description, selector);
      });
  }

  // If event deleted, ensure associated refvars are filtered
  filterQnodes(): void {
    const usedRefvars = [];
    const usedEvents = [];
    for (const event of this.events) {
      usedEvents.push(event);
      if (event.args) {
        for (const arg of event.args.filter((a) => a.refvar)) {
          usedRefvars.push(arg.refvar);
        }
      }
    }
    const newEventSelectors: QnodeSelector[] = [];
    const newEventSelectorMap: Map<string, QnodeSelector> = new Map();
    for (const usedEvent of usedEvents) {
      if (
        this.eventSelectorMap.has(usedEvent.event_text) &&
        !newEventSelectorMap.has(usedEvent.event_text)
      ) {
        const selector = this.eventSelectorMap.get(usedEvent.event_text);
        newEventSelectors.push(selector);
        newEventSelectorMap.set(usedEvent.event_text, selector);
      }
    }
    const newRefvarSelectorMap: Map<string, QnodeSelector> = new Map();
    const newRefvarSelectors: QnodeSelector[] = [];
    for (const usedRefvar of usedRefvars) {
      if (this.refvarSelectorMap.has(usedRefvar) && !newRefvarSelectorMap.has(usedRefvar)) {
        const selector = this.refvarSelectorMap.get(usedRefvar);
        newRefvarSelectors.push(selector);
        newRefvarSelectorMap.set(usedRefvar, selector);
      }
    }
    this.eventSelectorMap = newEventSelectorMap;
    this.eventSelectors = newEventSelectors;
    this.refvarSelectorMap = newRefvarSelectorMap;
    this.refvarSelectors = newRefvarSelectors;
  }

  // Triggered when the Add Event button is clicked, adds an event with input_text as event_text
  pushEvent(events: Event[]): void {
    this.events = events;
    for (const event of this.events) {
      this.getEventQnodes(event.event_text);
    }
    this.section_clear = true;
  }

  // Takes the changes made to the list of events and changes the graph accordingly
  refreshGraphNodes(): void {
    this.nodes = [];
    for (const event of this.events) {
      const node: Node = {
        id: event.event_text,
        label: event.id,
      };
      this.nodes.push(node);
    }

    // Remove dead links
    for (let i = 0; i < this.links.length; i++) {
      const link = this.links[i];
      if (
        this.nodes.findIndex((n) => n.id === link.source) === -1 ||
        this.nodes.findIndex((n) => n.id === link.target) === -1
      ) {
        this.links.splice(i, 1);
        i -= 1;
      }
    }
  }

  checkValidEvent(): void {
    if (this.events.length === 0) {
      this.toastr.error('Please enter at least one event.');
      throw new Error('No events provided.');
    }

    this.events.forEach((e) => {
      if (!e.event_primitive || !e.event_text) {
        this.toastr.error('All events must have a corresponding event primitive.');
        throw new Error('Events are incomplete.');
      }
    });
  }

  onClickNext(): void {
    this.checkValidEvent();
    this.filterQnodes();
    for (const e of this.events) {
      let id_str = '';
      id_str += 'E' + e.id_num.toString();

      if (e.event_text.length <= 25) {
        id_str += ' - ' + e.event_text;
      } else {
        id_str += ' - ' + e.event_text.slice(0, 22) + '...';
      }
      e.id = id_str;
    }
    this.refreshGraphNodes();
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
    const primitives = this.primitives;
    const rec_events = this.rec_events;
    const tracking = this.tracking;
    this.router.navigate(['/slot-and-order'], {
      state: {
        data: {
          events,
          nodes,
          links,
          clusters,
          node_ct,
          schema_id,
          schema_name,
          schema_dscpt,
          eventSelectors,
          eventSelectorMap,
          refvarSelectors,
          refvarSelectorMap,
          primitives,
          rec_events,
          tracking,
        },
      },
    });
  }

  redirectToSchemaLoader(): void {
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
    const primitives = this.primitives;
    const rec_events = this.rec_events;
    const tracking = this.tracking;
    this.router.navigate(['/load-schema'], {
      state: {
        data: {
          events,
          nodes,
          links,
          clusters,
          node_ct,
          schema_id,
          schema_name,
          schema_dscpt,
          eventSelectors,
          eventSelectorMap,
          refvarSelectors,
          refvarSelectorMap,
          primitives,
          rec_events,
          tracking,
        },
      },
    });
  }
}
