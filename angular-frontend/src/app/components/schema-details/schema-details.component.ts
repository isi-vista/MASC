import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-schema-details',
  templateUrl: './schema-details.component.html',
})
export class SchemaDetailsComponent {
  @Input() schema_id: string;
  @Input() schema_name: string;
  @Input() schema_dscpt: string;

  @Output() updateSchemaDetails: EventEmitter<{
    schema_id: string;
    schema_name: string;
    schema_dscpt: string;
  }> = new EventEmitter();

  editDetails = false;
  schema_id_temp: string;
  schema_name_temp: string;
  schema_dscpt_temp: string;

  constructor() {}

  startEditingDetails(): void {
    this.schema_id_temp = this.schema_id;
    this.schema_name_temp = this.schema_name;
    this.schema_dscpt_temp = this.schema_dscpt;
  }

  saveChanges(): void {
    this.schema_id = this.schema_id_temp;
    this.schema_name = this.schema_name_temp;
    this.schema_dscpt = this.schema_dscpt_temp;
    this.editDetails = false;
    this.updateSchemaDetails.emit({
      schema_id: this.schema_id,
      schema_name: this.schema_name,
      schema_dscpt: this.schema_dscpt,
    });
  }

  cancelChanges(): void {
    this.editDetails = false;
  }
}
