import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  DoCheck,
  ElementRef,
  EventEmitter,
  Input,
  IterableDiffer,
  IterableDiffers,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';
import { environment } from '../../../environments/environment';
import { Event } from '../../models/Event';
import { EventTablePageComponent } from '../event-table-page/event-table-page.component';
import { EventTableComponent } from '../event-table/event-table.component';

@Component({
  selector: 'app-event-suggestion',
  templateUrl: './event-suggestion.component.html',
  styleUrls: [],
})
export class EventSuggestionComponent implements DoCheck, OnInit {
  @ViewChild('popup') popup: ElementRef;
  @Input() suggest: boolean;
  @Output() suggestChange = new EventEmitter<boolean>();

  post_events: string[];
  recommendations: string[];
  has_error = false;
  differ: IterableDiffer<Event>;
  private apiUrl = environment.API_URL;

  constructor(
    private http: HttpClient,
    private toastr: ToastrService,
    public dialog: MatDialog,
    public eventTable: EventTablePageComponent,
    private differs: IterableDiffers,
    public realEventTable: EventTableComponent
  ) {
    this.differ = this.differs.find(this.eventTable.events).create();
  }

  async getResponse(): Promise<void> {
    this.has_error = false;
    this.realEventTable.data_loading = true;

    const params = {
      schema_name: this.eventTable.schema_name,
      schema_dscpt: this.eventTable.schema_dscpt,
      events: this.post_events,
    };

    this.eventTable.tracking.push({
      date: new Date().toISOString(),
      type: 'gpt2_suggestion_input',
      data: { input: params, mode: this.eventTable.schema_suggestion },
    });

    await this.http
      .get(this.apiUrl + '/api/get_gpt2_suggestions', {
        params,
      })
      .toPromise()
      .then((data) => {
        this.recommendations = data['suggestions'];
        this.eventTable.tracking.push({
          date: new Date().toISOString(),
          type: 'gpt2_suggestion_output',
          data: this.recommendations,
        });
      })
      .catch((error: HttpErrorResponse) => {
        console.error(error.message);
        this.has_error = true;
      })
      .finally(() => {
        this.updateSuggestLocal(false);
        this.realEventTable.data_loading = false;
      });
  }

  updateSuggestLocal(val: boolean): void {
    this.suggest = val;
    this.suggestChange.emit(this.suggest);
  }

  async initRecommendations(): Promise<void> {
    if (this.eventTable.events.length < 1) {
      this.recommendations = [];
    } else {
      await this.getResponse();
    }
  }

  selectEventSuggestion(value: { event_text: string }): void {
    this.realEventTable.input_text = value.event_text;
    this.eventTable.tracking.push({
      date: new Date().toISOString(),
      type: 'gpt2_suggestion_select',
      data: value.event_text,
    });
  }

  ngOnInit(): void {
    this.initRecommendations();
  }

  async ngDoCheck(): Promise<void> {
    if (this.eventTable.schema_suggestion === 'linear') {
      const change = this.differ.diff(this.eventTable.events);
      if (change) {
        this.post_events = [];
        this.eventTable.events.forEach((event: Event) => {
          this.post_events.push(event.event_text);
        });
        this.initRecommendations();
      }
    }

    if (this.eventTable.schema_suggestion === 'nonlinear') {
      if (this.suggest) {
        this.post_events = [];
        this.eventTable.events.forEach((event: Event) => {
          if (event.suggested) {
            this.post_events.push(event.event_text);
          }
        });
        if (this.post_events.length > 0) {
          await this.initRecommendations();
        } else {
          this.recommendations = [];
        }
        this.updateSuggestLocal(false);
      } else if (this.eventTable.section_clear) {
        this.recommendations = [];
        this.eventTable.section_clear = false;
      }
    }
  }
}
