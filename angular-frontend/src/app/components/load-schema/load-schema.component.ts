import { HttpClient, HttpParams } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ClusterNode, Edge, Node } from '@swimlane/ngx-graph';
import { ToastrService } from 'ngx-toastr';
import { environment } from '../../../environments/environment';
import { Event } from '../../models/Event';
import { QnodeSelector } from '../slot-and-order/slot-and-order.component';

export interface SchemaResponse {
  schema_id: string;
  schema_name: string;
  schema_dscpt: string;
  events: Event[];
  order: string[][];
  rec_events: string[][];
}

export interface SchemaFilesResponse {
  schemaFiles: string[];
}

@Component({
  selector: 'app-load-schema',
  templateUrl: './load-schema.component.html',
  styleUrls: ['./load-schema.component.css'],
})
export class LoadSchemaComponent implements OnInit {
  events: Event[];

  nodes: Node[];
  links: Edge[];
  clusters: ClusterNode[];
  node_ct: number;
  schema_id: string;
  schema_name: string;
  schema_dscpt: string;
  eventSelectors: QnodeSelector[] = [];
  eventSelectorMap: Map<string, QnodeSelector> = new Map();
  refvarSelectors: QnodeSelector[] = [];
  refvarSelectorMap: Map<string, QnodeSelector> = new Map();
  rec_events: string[][];
  savedSchemas: string[];
  selectedSchema: string;
  tracking: { date: string; type: string; data: unknown }[];

  schemaSearchQuery: string;

  schemaFile: string;
  private apiUrl = environment.API_URL;

  constructor(private http: HttpClient, private router: Router, private toastr: ToastrService) {
    // Listen for reloads and warn user when reloading page
    window.addEventListener('beforeunload', (event) => {
      // Most browsers might override this and present a generic message
      event.returnValue =
        'Are you sure you want to leave? All unsaved/unsubmitted data will be lost';
    });

    // Storing these variables to make the app persistent across pages
    // can possibly be removed when cookies are added
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
    }
  }

  ngOnInit(): void {
    this.getSavedSchemas();
  }

  async requestSavedSchemas(): Promise<void> {
    return this.http
      .get(this.apiUrl + '/api/get_saved_schemas')
      .toPromise()
      .then((data: SchemaFilesResponse) => {
        this.savedSchemas = data.schemaFiles;
      });
  }
  async getSavedSchemas(): Promise<void> {
    await this.requestSavedSchemas();
  }

  relevantSearchQuery(schema: LoadSchemaComponent): boolean {
    if (this.schemaSearchQuery === undefined) {
      return true;
    }
    return (
      schema.schema_id.search(this.schemaSearchQuery) >= 0 ||
      schema.schema_name.search(this.schemaSearchQuery) >= 0 ||
      schema.schema_dscpt.search(this.schemaSearchQuery) >= 0
    );
  }

  setQnodes(): void {
    for (const event of this.events) {
      if (event.reference) {
        const eventSelector: QnodeSelector = {
          query: event.event_text,
          options: [],
          qnode: event.reference,
          selectedQnode: event.reference,
        };
        this.eventSelectors.push(eventSelector);
        this.eventSelectorMap.set(event.event_text, eventSelector);
      }
      if (event.args) {
        for (const arg of event.args.filter((a) => a.reference)) {
          if (!this.refvarSelectorMap.has(arg.refvar)) {
            const selector: QnodeSelector = {
              query: arg.refvar,
              options: [],
              qnode: arg.reference,
              selectedQnode: arg.reference,
            };
            this.refvarSelectors.push(selector);
            this.refvarSelectorMap.set(arg.refvar, selector);
          }
        }
      }
    }
  }

  createLinks(order_pairs: string[][]): void {
    this.links = [];
    for (const order_pair of order_pairs) {
      const source_id_num = this.events
        .find((e) => e.event_text === order_pair[0])
        .id_num.toString();
      const target_id_num = this.events
        .find((e) => e.event_text === order_pair[1])
        .id_num.toString();
      const link_id: string = 'E' + source_id_num + '-E' + target_id_num;
      const link: Edge = {
        id: link_id,
        source: order_pair[0],
        target: order_pair[1],
        label: '',
      };
      this.links.push(link);
    }
  }

  async fetchSchema(): Promise<void> {
    this.eventSelectors = [];
    this.eventSelectorMap = new Map();
    this.refvarSelectors = [];
    this.refvarSelectorMap = new Map();
    let query = new HttpParams();
    query = query.set('schemaFile', this.selectedSchema);
    return this.http
      .get(this.apiUrl + '/api/get_schema', { params: query })
      .toPromise()
      .then((data: SchemaResponse) => {
        this.events = data.events;
        this.createLinks(data.order);
        this.schema_id = data.schema_id;
        this.schema_name = data.schema_name;
        this.schema_dscpt = data.schema_dscpt;
        this.schemaFile = null;
        this.node_ct = this.events.length;
        this.rec_events = data.rec_events;
        this.tracking = [];
        this.setQnodes();
      }); // Graph nodes are created when the Next Page button is clicked and the refreshGraphNodes() function is called
  }

  redirectToEventTable(): void {
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
          schema_id,
          schema_name,
          schema_dscpt,
          eventSelectors,
          eventSelectorMap,
          refvarSelectors,
          refvarSelectorMap,
          rec_events,
          tracking,
        },
      },
    });
  }

  async getSchema(): Promise<number> {
    if (this.selectedSchema === undefined) {
      this.toastr.error('No schema selected.');
      return 0;
    }

    // Fetch schema from server
    await this.fetchSchema();

    // Redirect after loading schema
    this.redirectToEventTable();
    return 0;
  }
}
