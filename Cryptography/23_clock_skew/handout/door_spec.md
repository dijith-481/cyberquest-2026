FACILITIES BULLETIN - EAST STAIRWELL DOOR (MODEL FAC-DOOR-4)

The east stairwell door accepts a six-digit rotating code. The door
implements the standard rotating-code scheme exactly as specified:

  - codes are derived with HMAC-SHA1;
  - the time step is 30 seconds;
  - the code is the standard 6-digit dynamic truncation of the HMAC
    output, decimal, zero-padded;
  - the key is the door's 6-digit enrollment code, used verbatim as the
    HMAC key (the digits themselves, as text).

Enrollment codes are six digits, 0-9, assigned by facilities at install
time and changed only at install time.

The door's clock is wrong. It has been wrong since the power event in
February, it is wrong by whole minutes, and it remains wrong on purpose:
facilities has a ticket open. The ticket has a number. The number is not
written down anywhere, much like the enrollment code.

Codes are shown on the maintenance panel and accepted for one time
step. If the clock says it is a valid moment, the door agrees.
