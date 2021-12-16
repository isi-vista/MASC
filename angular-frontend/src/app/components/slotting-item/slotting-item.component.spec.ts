import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SlottingItemComponent } from './slotting-item.component';

describe('SlottingItemComponent', () => {
  let component: SlottingItemComponent;
  let fixture: ComponentFixture<SlottingItemComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [SlottingItemComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SlottingItemComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
