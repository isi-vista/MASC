import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EventTablePageComponent } from './event-table-page.component';

describe('EventTablePageComponent', () => {
  let component: EventTablePageComponent;
  let fixture: ComponentFixture<EventTablePageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [EventTablePageComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(EventTablePageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
