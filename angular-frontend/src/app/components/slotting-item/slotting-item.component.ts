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
import { ToastrService } from 'ngx-toastr';
import { environment } from '../../../environments/environment';
import { Arg } from '../../models/Arg';
import { Event } from '../../models/Event';
import { Primitive } from '../../models/Primitive';

export interface SlotReponse {
  slots: string[];
  constraints: string[];
}

@Component({
  // eslint-disable-next-line @angular-eslint/component-selector
  selector: '[app-slotting-item]',
  templateUrl: './slotting-item.component.html',
  styleUrls: ['./slotting-item.component.css'],
})
export class SlottingItemComponent implements OnInit {
  @Input() event: Event;
  @Input() event_index: number;
  @ViewChild('popup') popup: ElementRef;
  @Output() slotChange: EventEmitter<string[]> = new EventEmitter<string[]>();

  role: string;
  refvar: string;
  constraints: string[];
  response: SlotReponse;
  primitive: Primitive;
  arg: Arg;
  private apiUrl = environment.API_URL;

  constructor(private http: HttpClient, private toastr: ToastrService) {
    // Initializing refvar. without this, the first arg added for an event lacks
    // the refvar field altogether (if the refvar field is left empty)
    this.refvar = null;
  }

  async getSlotResponse(primitive: string): Promise<void> {
    let query = new HttpParams();
    query = query.set('event_primitive', primitive);
    await this.http
      .get(this.apiUrl + '/api/get_slots', { params: query })
      .toPromise()
      .then((data: SlotReponse) => {
        this.response = data;
      });
  }

  async initSlots(): Promise<void> {
    await this.getSlotResponse(this.event.event_primitive);
    const a = [];
    for (let i = 0; i < this.response.slots.length; i++) {
      a.push({ role: this.response.slots[i], constraints: this.response.constraints[i] });
    }
    this.primitive = {
      type: this.event.event_primitive,
      subtype: 'S',
      subsubtype: 'SS',
      description: 'temp',
      args: a,
    };
  }

  onClickClose(): void {
    this.role = null;
    this.refvar = null;
    this.constraints = null;
    this.arg = null;
  }

  ngOnInit(): void {
    this.initSlots();
  }

  deleteSlot(role: string, refvar: string): void {
    this.event.args = this.event.args.filter((a) => a.role !== role || a.refvar !== refvar);
    this.slotChange.emit([refvar]);
  }

  onClickOpen(arg: Arg): void {
    this.role = arg.role;
    this.refvar = arg.refvar;
    this.constraints = arg.constraints;
    this.arg = arg;
  }

  getCommonConstraints(): string[] {
    let commonConstraints = [];
    this.primitive.args.forEach((arg) => {
      if (this.role === arg.role) {
        commonConstraints = arg.constraints;
      }
    });
    return commonConstraints;
  }

  saveSlot(): number {
    // Refvar validation
    if (!this.refvar || !this.refvar.trim().length) {
      this.toastr.error('Empty strings are not allowed.');
      return 0;
    }

    for (const arg of this.event.args) {
      if (
        arg.role === this.arg.role &&
        arg.refvar === this.arg.refvar &&
        arg.role === this.arg.role
      ) {
        const oldRefvar = arg.refvar;
        arg.role = this.role;
        arg.refvar = this.refvar;
        arg.constraints = this.constraints;
        if (oldRefvar && this.refvar) {
          this.slotChange.emit([this.refvar, oldRefvar]);
        }
      }
    }
    this.onClickClose();
    return 0;
  }
}
