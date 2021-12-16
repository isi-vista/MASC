import { Arg } from './Arg';

export class Primitive {
  type: string;
  subtype?: string;
  subsubtype?: string;
  subsubtypes?: string[];
  description?: string;
  args?: Arg[];
}
