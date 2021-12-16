import { HttpClient, HttpParams } from '@angular/common/http';
import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';
import { environment } from '../../../environments/environment';
import { Event } from '../../models/Event';
import { Primitive } from '../../models/Primitive';
import { EventTableComponent } from '../event-table/event-table.component';
import { ConfirmPopupComponent } from '../modals/confirm-popup/confirm-popup.component';

@Component({
  // eslint-disable-next-line @angular-eslint/component-selector
  selector: '[app-event-item]',
  templateUrl: './event-item.component.html',
  styleUrls: ['./event-item.component.css'],
})
export class EventItemComponent implements OnInit {
  @Input() event: Event;
  @Input() primitives: Primitive[];
  @Output() deleteEvent: EventEmitter<Event> = new EventEmitter();
  @Output() disambiguateEvent: EventEmitter<string> = new EventEmitter();

  @ViewChild('popup') popup: ElementRef;

  // The event primitive type, subtype, subsubtypes are directly bound to the form values
  descriptionEditing = false;
  tempDescription = ' '; // Going to use this for
  recommendations: Primitive[];
  response: Primitive[];
  private apiUrl = environment.API_URL;

  constructor(
    private http: HttpClient,
    private toastr: ToastrService,
    public eventTable: EventTableComponent,
    public dialog: MatDialog
  ) {}

  async getResponse(description: string): Promise<void> {
    let query = new HttpParams();
    query = query.set('event_description', description);
    await this.http
      .get(this.apiUrl + '/api/get_top3', { params: query })
      .toPromise()
      .then((data: Primitive[]) => {
        this.response = data;
      });
  }

  async initRecommendations(): Promise<void> {
    // Get recommendations for primitives
    await this.getResponse(this.event.event_text);
    this.recommendations = this.response;
    this.disambiguateEvent.emit(this.event.event_text);
  }

  ngOnInit(): void {
    this.initRecommendations();
  }

  onClickOpen(): void {
    const popup_native = this.popup.nativeElement;
    popup_native.style.display = 'block';
  }

  onClickClose(): void {
    const popup_native = this.popup.nativeElement;
    popup_native.style.display = 'none';
  }

  onClickSelect(value: { primitive: string }): void {
    const prim_idx = this.recommendations.findIndex((e) => e.type === value.primitive);
    const idx = Math.max(
      this.recommendations[prim_idx].subsubtypes.findIndex((s) => s === 'Unspecified'),
      0
    );
    // Unspecified if it is a valid subsubtype, first subsubtype otherwise
    this.event.event_primitive =
      value.primitive + '.' + this.recommendations[prim_idx].subsubtypes[idx];
    const popup_native = this.popup.nativeElement;
    popup_native.style.display = 'none';
  }

  onDelete(event: Event): void {
    const dialogRef = this.dialog.open(ConfirmPopupComponent, {
      maxWidth: '400px',
      data: {
        title: 'Are you sure you want to delete this event?',
      },
    });

    // Wait for response
    dialogRef.afterClosed().subscribe((dialogResult) => {
      if (dialogResult) {
        this.deleteEvent.emit(event);
      }
    });
  }

  deselectPrimitive(): void {
    this.event.event_primitive = null;
    this.event.args = undefined;
  }

  startEditing(): void {
    this.descriptionEditing = true;
    this.tempDescription = this.event.event_text;
  }

  finishEditing(): number {
    // Need to add validation here, thinking of best way to do that.
    if (this.isDuplicate() && this.tempDescription !== this.event.event_text) {
      this.toastr.error('Event ID already used. Duplicate events are not allowed');
      this.tempDescription = this.event.event_text;
      this.descriptionEditing = false;
      return -1;
    }
    this.eventTable.tracking.push({
      date: new Date().toISOString(),
      type: 'edit_event',
      data: { old_text: this.event.event_text, new_text: this.tempDescription },
    });
    this.event.event_text = this.tempDescription;
    this.descriptionEditing = false;
    return 0;
  }

  isDuplicate(): boolean {
    for (const event of this.eventTable.events) {
      if (event.event_text.replace(/ /g, '-') === this.tempDescription.replace(/ /g, '-')) {
        return true;
      }
    }
    return false;
  }
}
