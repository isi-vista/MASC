import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EventrecTableComponent } from './eventrec-table.component';

describe('EventrecTableComponent', () => {
  let component: EventrecTableComponent;
  let fixture: ComponentFixture<EventrecTableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [EventrecTableComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(EventrecTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
