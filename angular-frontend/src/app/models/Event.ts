import { Arg } from './Arg';

export class Event {
  event_text: string;
  event_primitive: string; // String of the form "type.subtype.subsubtype"
  comment?: string;
  id?: string;
  id_num?: number;
  node_id?: number;
  args?: Arg[];
  is_checked?: boolean;
  staged_arg?: string;
  staged_constraints?: string[];
  required?: boolean;
  suggested?: boolean;
  after?: string;
  reference?: string;
}
