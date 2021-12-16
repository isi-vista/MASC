import { Component, Input } from '@angular/core';
import { QnodeSelector } from '../../slot-and-order/slot-and-order.component';

@Component({
  selector: 'app-linking-popup',
  templateUrl: './linking-popup.component.html',
  styleUrls: [],
})
export class LinkingPopupComponent {
  @Input() selectors: QnodeSelector[];
  constructor() {}

  onClose(save: boolean): void {
    for (const selector of this.selectors) {
      if (save) {
        selector.qnode = selector.selectedQnode;
      } else {
        selector.selectedQnode = selector.qnode;
      }
    }
  }
}
