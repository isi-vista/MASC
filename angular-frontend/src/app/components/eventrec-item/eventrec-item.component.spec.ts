import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EventrecItemComponent } from './eventrec-item.component';

describe('EventrecItemComponent', () => {
  let component: EventrecItemComponent;
  let fixture: ComponentFixture<EventrecItemComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [EventrecItemComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(EventrecItemComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
