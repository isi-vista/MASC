import { DragDropModule } from '@angular/cdk/drag-drop';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatDialogModule } from '@angular/material/dialog';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { NgxGraphModule } from '@swimlane/ngx-graph';
import { ToastrModule } from 'ngx-toastr';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { ArgSelectComponent } from './components/arg-select/arg-select.component';
import { EventItemComponent } from './components/event-item/event-item.component';
import { EventSuggestionComponent } from './components/event-suggestion/event-suggestion.component';
import { EventTablePageComponent } from './components/event-table-page/event-table-page.component';
import { EventTableComponent } from './components/event-table/event-table.component';
import { EventrecItemComponent } from './components/eventrec-item/eventrec-item.component';
import { EventrecTableComponent } from './components/eventrec-table/eventrec-table.component';
import { LoadSchemaComponent } from './components/load-schema/load-schema.component';
import { ConfirmPopupComponent } from './components/modals/confirm-popup/confirm-popup.component';
import { LinkingPopupComponent } from './components/modals/linking-popup/linking-popup.component';
import { SchemaDetailsComponent } from './components/schema-details/schema-details.component';
import { SlotAndOrderComponent } from './components/slot-and-order/slot-and-order.component';
import { SlottingItemComponent } from './components/slotting-item/slotting-item.component';

@NgModule({
  declarations: [
    AppComponent,
    EventSuggestionComponent,
    EventTableComponent,
    EventItemComponent,
    SlotAndOrderComponent,
    SlottingItemComponent,
    ArgSelectComponent,
    ConfirmPopupComponent,
    EventrecItemComponent,
    EventrecTableComponent,
    LoadSchemaComponent,
    LinkingPopupComponent,
    EventTablePageComponent,
    SchemaDetailsComponent,
  ],
  imports: [
    BrowserModule,
    ToastrModule.forRoot(),
    AppRoutingModule,
    FormsModule,
    NgxGraphModule,
    BrowserAnimationsModule,
    HttpClientModule,
    MatCardModule,
    MatDialogModule,
    DragDropModule,
  ],
  providers: [],
  bootstrap: [AppComponent],
})
export class AppModule {}
