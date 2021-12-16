import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { HttpClient } from '@angular/common/http';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { Router } from '@angular/router';
import { Node } from '@swimlane/ngx-graph';
import { ToastrService } from 'ngx-toastr';
import { environment } from '../../../environments/environment';
import { Event } from '../../models/Event';
import { Primitive } from '../../models/Primitive';

export interface RecommendationsResponse {
  primitives: Primitive[];
}

@Component({
  selector: 'app-event-table',
  templateUrl: './event-table.component.html',
  styleUrls: ['./event-table.component.css'],
})
export class EventTableComponent implements OnInit {
  @Input() hasSchemaDetails = false;
  @Input() schema_suggestion = 'linear';
  @Output() pushEvent: EventEmitter<Event[]> = new EventEmitter();
  @Output() filterQnodes: EventEmitter<void> = new EventEmitter();

  primitives: Primitive[];

  events: Event[];
  input_text: string;

  nodes: Node[];
  node_ct: number;

  response: RecommendationsResponse;
  tracking: { date: string; type: string; data: unknown }[];
  private apiUrl = environment.API_URL;

  // Event suggestion variables
  event_suggestion: boolean;
  suggest = false;
  data_loading = false;

  constructor(private http: HttpClient, private router: Router, private toastr: ToastrService) {
    if (history.state.data === undefined) {
      this.events = [];
      this.nodes = [];
      this.node_ct = 0;
      this.tracking = [];
    } else {
      this.events = history.state.data.events;
      this.node_ct = history.state.data.node_ct;
      this.nodes = history.state.data.nodes;
      this.tracking = history.state.data.nodes;
    }
    this.event_suggestion = router.url === '/event-suggestion';
  }

  drop(event: CdkDragDrop<string[]>): void {
    moveItemInArray(this.events, event.previousIndex, event.currentIndex);
    this.tracking.push({
      date: new Date().toISOString(),
      type: 'reorder_event',
      data: { old_index: event.previousIndex, new_index: event.currentIndex },
    });
  }

  isDuplicate(): boolean {
    for (const event of this.events) {
      if (event.event_text.replace(/ /g, '-') === this.input_text.replace(/ /g, '-')) {
        return true;
      }
    }
    return false;
  }

  onSuggest(): void {
    this.suggest = true;
  }

  // Triggered when the Add Event button is clicked, adds an event with input_text as event_text
  addEvent(): number {
    if (this.input_text === null || this.input_text === undefined) {
      this.toastr.error('Invalid event ID entered. Empty strings are not allowed.', '', {
        timeOut: 1500,
      });
      return -1;
    }
    this.input_text = this.input_text.trim();
    if (this.isDuplicate()) {
      this.toastr.error('Event already exists. Duplicate events cannot be added');
      return -1;
    }

    const input_event: Event = {
      event_text: this.input_text,
      event_primitive: null,
      id_num: this.node_ct + 1,
      is_checked: false,
      required: true,
      suggested: true,
    };
    this.events.push(input_event);
    this.pushEvent.emit(this.events);
    this.node_ct += 1;
    this.input_text = null;
    this.tracking.push({
      date: new Date().toISOString(),
      type: 'add_event',
      data: input_event.event_text,
    });
    return 0;
  }

  // Function that takes input from the EventEmitter of a row from the event-item component and deletes the corresponding event
  deleteEvent(event: Event): void {
    // Since nodes are created only after the primitive is assigned to an event
    if (event.event_primitive !== null && event.event_primitive !== undefined) {
      const idx = this.nodes.findIndex((n) => n.id === event.event_text);
      this.nodes.splice(idx, 1);
    }

    const index = this.events.findIndex((e) => e.event_text === event.event_text);
    this.events.splice(index, 1);
    this.filterQnodes.emit();
    this.tracking.push({
      date: new Date().toISOString(),
      type: 'delete_event',
      data: event.event_text,
    });
  }

  async getAllPrimitives(): Promise<void> {
    return this.http
      .get(this.apiUrl + '/api/get_all_primitives')
      .toPromise()
      .then((data: RecommendationsResponse) => {
        this.response = data;
      });
  }

  async initPrimitiveList(): Promise<void> {
    await this.getAllPrimitives();
    this.primitives = [];
    for (const primitive of this.response.primitives) {
      const p: Primitive = {
        type: primitive.type,
        subsubtypes: primitive.subsubtypes,
        description: primitive.description,
      };
      this.primitives.push(p);
    }
  }

  ngOnInit(): void {
    this.initPrimitiveList();
  }
}
