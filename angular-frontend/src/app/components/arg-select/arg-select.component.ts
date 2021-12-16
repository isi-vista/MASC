import { HttpClient, HttpParams } from '@angular/common/http';
import { Component, Input, OnInit } from '@angular/core';
import { environment } from '../../../environments/environment';
import { Event } from '../../models/Event';
import { Primitive } from '../../models/Primitive';

export interface SlotResponse {
  slots: string[];
  constraints: string[];
}

@Component({
  selector: 'app-arg-select',
  templateUrl: './arg-select.component.html',
  styleUrls: [],
})
export class ArgSelectComponent implements OnInit {
  @Input() event: Event;

  display_string: string;

  response: SlotResponse;
  primitive: Primitive;
  private apiUrl = environment.API_URL;

  constructor(private http: HttpClient) {
    this.primitive = null;
  }

  async getResponse(): Promise<void> {
    let query = new HttpParams();
    query = query.set('event_primitive', this.event.event_primitive);
    await this.http
      .get(this.apiUrl + '/api/get_slots', { params: query })
      .toPromise()
      .then((data: SlotResponse) => {
        this.response = data;
      });
  }

  async initSlots(): Promise<void> {
    await this.getResponse();
    const a = [];
    for (let i = 0; i < this.response.slots.length; i++) {
      a.push({ role: this.response.slots[i], constraints: this.response.constraints[i] });
      this.primitive = {
        type: this.event.event_primitive,
        subtype: 'S',
        subsubtype: 'SS',
        description: 'temp',
        args: a,
      };
    }
  }

  ngOnInit(): void {
    this.event.staged_arg = null;
    this.display_string = 'E' + this.event.id_num;

    if (this.event.event_text.length <= 25) {
      this.display_string += ' - ' + this.event.event_text;
    } else {
      this.display_string += ' - ' + this.event.event_text.slice(0, 25) + '...';
    }
    this.initSlots();
  }

  onChange(): void {
    const arg = this.primitive.args.find((a) => a.role === this.event.staged_arg);
    this.event.staged_constraints = arg.constraints;
  }
}
