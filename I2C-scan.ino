#include <Wire.h>

void setup() {
  delay(500);
  Wire.begin();

  Serial.begin (115200);
  delay(500);

  Serial.println ("John's I2C scanner. Scanning ...");
  byte count = 0;
  do {
    for (byte i = 0; i < 120; i++)
    {

      Wire.beginTransmission (i);
      if (Wire.endTransmission () == 0)
      {
        Serial.print ("Found address: ");
        Serial.print (i, DEC);
        Serial.print (" (0x");
        Serial.print (i, HEX);
        Serial.println (")");
        count++;
        delay (1);  // maybe unneeded?
      } // end of good response
    } // end of for loop
    Serial.println ("Done.");
    Serial.print ("Found ");
    Serial.print (count, DEC);
    Serial.println (" device(s).");
    delay(5000);

  } while (true);
}


void loop() {
  // put your main code here, to run repeatedly:

}
