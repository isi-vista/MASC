import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LinkingPopupComponent } from './linking-popup.component';

describe('LinkingPopupComponent', () => {
  let component: LinkingPopupComponent;
  let fixture: ComponentFixture<LinkingPopupComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [LinkingPopupComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LinkingPopupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
