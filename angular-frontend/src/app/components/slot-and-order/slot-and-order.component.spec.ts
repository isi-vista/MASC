import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SlotAndOrderComponent } from './slot-and-order.component';

describe('SlotAndOrderComponent', () => {
  let component: SlotAndOrderComponent;
  let fixture: ComponentFixture<SlotAndOrderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [SlotAndOrderComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SlotAndOrderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
