void setup() {
  pinMode(1,OUTPUT);
  pinMode(2,OUTPUT);
  pinMode(2,OUTPUT);
  pinMode(8,INPUT);
  pinMode(9,INPUT);
  pinMode(10,INPUT);

    Serial.begin(9600);
}

void loop() {
    int btn1,btn2,btn3
    int btn1_state = 0;
    int btn2_state = 0;
    int btn3_state = 0;
    btn1 = digitalRead(8);
    if(btn1 == 1 && btn1_state == 0){
        btn1_state = 1;
        digitalWrite(1,HIGH);
    }
    if(btn1 == 0 && btn1_state == 1){
        btn1_state = 0;
        digitalWrite(1,LOW);
    }
}