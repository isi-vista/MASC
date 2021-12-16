import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LoadSchemaComponent } from './load-schema.component';

describe('LoadSchemaComponent', () => {
  let component: LoadSchemaComponent;
  let fixture: ComponentFixture<LoadSchemaComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [LoadSchemaComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LoadSchemaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
