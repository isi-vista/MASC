import { HttpClient, HttpParams } from '@angular/common/http';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { environment } from '../../../environments/environment';
import { Event } from '../../models/Event';
import { Primitive } from '../../models/Primitive';

@Component({
  // eslint-disable-next-line @angular-eslint/component-selector
  selector: '[app-eventrec-item]',
  templateUrl: './eventrec-item.component.html',
  styleUrls: [],
})
export class EventrecItemComponent implements OnInit {
  @Input() event: Event;
  @Input() primitives: Primitive[];
  @Output() addEventRec: EventEmitter<{ event: Event; addlink: boolean }> = new EventEmitter();

  recommendations: Primitive[];
  response: Primitive[];
  private apiUrl = environment.API_URL;

  constructor(private http: HttpClient, private toastr: ToastrService) {}

  async getResponse(description: string): Promise<void> {
    let query = new HttpParams();
    query = query = query.set('event_description', description);
    await this.http
      .get(this.apiUrl + '/api/get_top3', { params: query })
      .toPromise()
      .then((data: Primitive[]) => {
        this.response = data;
      });
  }

  async initRecommendations(): Promise<void> {
    await this.getResponse(this.event.event_text);
    this.recommendations = this.response;
  }

  ngOnInit(): void {
    this.initRecommendations();
  }

  deselectPrimitive(): void {
    this.event.event_primitive = null;
    this.event.args = undefined;
  }

  onAddEventRec(event: Event, addlink: boolean): void {
    if (!event.event_primitive) {
      this.toastr.error('All events must have a corresponding event primitive.');
      throw new Error('Events are incomplete.');
    } else {
      const emit_bundle: { event: Event; addlink: boolean } = {
        event,
        addlink,
      };
      this.addEventRec.emit(emit_bundle);
    }
  }
}
