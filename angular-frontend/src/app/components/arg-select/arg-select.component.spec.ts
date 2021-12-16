import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ArgSelectComponent } from './arg-select.component';

describe('ArgSelectComponent', () => {
  let component: ArgSelectComponent;
  let fixture: ComponentFixture<ArgSelectComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ArgSelectComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ArgSelectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
