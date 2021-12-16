import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { Edge, Node } from '@swimlane/ngx-graph';
import { ToastrService } from 'ngx-toastr';
import { Event } from '../../models/Event';
import { Primitive } from '../../models/Primitive';

@Component({
  selector: 'app-eventrec-table',
  templateUrl: './eventrec-table.component.html',
  styleUrls: ['./eventrec-table.component.css'],
})
export class EventrecTableComponent implements OnInit {
  // eslint-disable-next-line capitalized-comments
  // events and node_ct have to be inputted
  @Input() events: Event[];
  @Input() rec_events: string[][];
  @Input() nodes: Node[];
  @Input() links: Edge[];
  @Input() node_ct: number;
  @Input() primitives: Primitive[];
  @Output() addNode: EventEmitter<{ event: Event; addlink: boolean }> = new EventEmitter();

  event_recs: Event[]; // TODO: get event recommendations

  constructor(private toastr: ToastrService) {}

  ngOnInit(): void {
    this.event_recs = [];
    let ctr = 0; // Counter used to add temporary id_num for event recommendations

    for (const e of this.rec_events) {
      const idx = this.events.findIndex((eve) => eve.event_text === e[0]);
      let after_str = '';
      if (idx !== -1) {
        after_str = 'E' + this.events[idx].id_num.toString();
        if (this.events[idx].event_text.length <= 10) {
          after_str += ' - ' + this.events[idx].event_text;
        } else {
          after_str += ' - ' + this.events[idx].event_text.slice(0, 9) + '...';
        }
      } else {
        after_str = 'DNE';
      }

      for (let i = 1; i < e.length; i++) {
        const event: Event = {
          event_text: e[i],
          event_primitive: null,
          after: after_str,
          id_num: ctr,
          required: false,
        };
        this.event_recs.push(event);
        ctr += 1;
      }
    }
  }

  deleteEventRec(event: Event): void {
    const index = this.event_recs.findIndex((e) => e.event_text === event.event_text);
    this.event_recs.splice(index, 1);
  }

  isDuplicate(event: Event): boolean {
    for (const e of this.events) {
      if (e.event_text.replace(/ /g, '-') === event.event_text.replace(/ /g, '-')) {
        return true;
      }
    }
    return false;
  }

  addEventRec(emit_bundle: { event: Event; addlink: boolean }): number {
    const event = emit_bundle.event;
    const addlink = emit_bundle.addlink;
    if (this.isDuplicate(event)) {
      this.toastr.error('Event already exists. Duplicate events cannot be added');
      return -1;
    }

    let id_str = '';
    id_str += 'E' + (this.node_ct + 1).toString();

    if (event.event_primitive.split('.')[1].length <= 15) {
      id_str += ' - ' + event.event_primitive.split('.')[1];
    } else {
      id_str += ' - ' + event.event_primitive.split('.')[1].slice(0, 11) + '...';
    }

    if (event.event_text.length <= 10) {
      id_str += ' - ' + event.event_text;
    } else {
      id_str += ' - ' + event.event_text.slice(0, 9) + '...';
    }

    const input_event: Event = {
      event_text: event.event_text,
      event_primitive: event.event_primitive,
      id_num: this.node_ct + 1,
      id: id_str,
      is_checked: false,
      required: event.required,
    };
    this.events.push(input_event);
    this.node_ct += 1;

    this.deleteEventRec(event);
    const link_bundle: { event: Event; addlink: boolean } = {
      event: input_event,
      addlink,
    };
    this.addNode.emit(link_bundle);
    return 0;
  }
}
