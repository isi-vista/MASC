import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { EventTablePageComponent } from './components/event-table-page/event-table-page.component';
import { LoadSchemaComponent } from './components/load-schema/load-schema.component';
import { SlotAndOrderComponent } from './components/slot-and-order/slot-and-order.component';

const routes: Routes = [
  { path: 'add-events', component: EventTablePageComponent },
  { path: 'event-suggestion', component: EventTablePageComponent },
  { path: 'slot-and-order', component: SlotAndOrderComponent },
  { path: '', component: EventTablePageComponent },
  { path: 'load-schema', component: LoadSchemaComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
