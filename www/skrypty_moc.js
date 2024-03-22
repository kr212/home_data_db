//generowanie umikalnego identyfikatora
function uuid() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
  }

function toISO(date)
{
  //change date to iso string
  let month=String(date.getMonth()+1);
  if (month.length==1){
    month='0'+month;
  }

  let day=String(date.getDate());
  if (day.length==1){
    day='0'+day;
  }

  let hours=String(date.getHours());
  if (hours.length==1){
    hours='0'+hours;
  }

  let minutes=String(date.getMinutes());
  if (minutes.length==1){
    minutes='0'+minutes;
  }

  let seconds=String(date.getSeconds());
  if (seconds.length==1){
    seconds='0'+seconds;
  }
  let txt=String(date.getFullYear())+'-'+month+'-'+day+' '+hours+':'+minutes+':'+seconds;

  return txt;
}
//set data on page

//ustawienie odebranych danych na stronie - moc chwilowa
function set_power(dane) {
    
    
    pole=document.getElementById("power_field");
    pole.innerHTML=String(dane['value'])+" kW";

    let date=new Date(dane['time']);

    Plotly.extendTraces('plot',{x:[[date]],y:[[dane['value']]]},[0]);
    //Plotly.update('plot',{value: parseFloat(data_spl[0])},{});
    
}

//button functions
function generate_plots_hours() {
    //button from hours pressed
    let hours=document.getElementById("last_hours");
    let time= new Date();

    //remove miliseconds
    let date_time_to=toISO(time);

    let h=parseInt(hours.value);

    if (h<1)
    {
      h=1;
    }

    let tmp=new Date(time-h*60*60*1000); //shift in ms - 1 hour

    let date_time_from=toISO(tmp);


    client.publish('storage/control',JSON.stringify({'command':'get_data','type':'time_record','variable':'power','date_time_from':date_time_from,'date_time_to':date_time_to,'answer_to':uuid_num}))

}


function generate_plots_days() {
  //button from hours pressed
  let days=document.getElementById("last_days");
  let time= new Date();

  //remove miliseconds
  let date_time_to=toISO(time);

  let d=parseInt(days.value);

  if (d<1)
  {
    d=1;
  }

  let tmp=new Date(time-d*60*60*1000*24); //shift in ms - 1 day

  let date_time_from=toISO(tmp);


  client.publish('storage/control',JSON.stringify({'command':'get_data','type':'time_record','variable':'power','date_time_from':date_time_from,'date_time_to':date_time_to,'answer_to':uuid_num}))

}

function generate_plots() {
  //button from hours pressed
  let fdate_from=document.getElementById("date_from");
  let fdate_to=document.getElementById("date_to");
  let ftime_from=document.getElementById("time_from");
  let ftime_to=document.getElementById("time_to");
  
  let date_time_from=fdate_from.value+' '+ftime_from.value;
  let date_time_to=fdate_to.value+' '+ftime_to.value;


  client.publish('storage/control',JSON.stringify({'command':'get_data','type':'time_record','variable':'power','date_time_from':date_time_from,'date_time_to':date_time_to,'answer_to':uuid_num}))

}

//MQTT functions
// called when the client connects
function onConnect() {
    // Once a connection has been made, make a subscription and send a message.
    console.log("onConnect");
    //client.subscribe("World");
    client.subscribe('meter/data/power_mom');
    //client.subscribe('mcp/data/temp_water');
    //client.subscribe('mcp/data/temp_outside');
    //client.subscribe('mcp/data/pressure');
    client.subscribe('storage/data/'+uuid_num)
    // message = new Paho.MQTT.Message("Hello");
    // message.destinationName = "World";
    // client.send(message);
  }
  
  // called when the client loses its connection
function onConnectionLost(responseObject) {
    if (responseObject.errorCode !== 0) {
      console.log("onConnectionLost:"+responseObject.errorMessage);
    }
}
  
  // called when a message arrives
function onMessageArrived(message) {
    console.log("onMessageArrived:"+message.destinationName+" : "+message.payloadString);
    if (message.destinationName=='meter/data/power_mom') {
      set_power(JSON.parse(message.payloadString))
    }
    else if (message.destinationName=='storage/data/'+uuid_num)
    {
      //got data for plot
      let payload = JSON.parse(message.payloadString)
    
      //what kind of plot have to generate
      switch (payload['data_type'])
      {
          case 'time_record':
            if (payload['data']['variable']=='power')
            {
                
                plotHistory(payload['data']);
            }
              //plotBarDayConsumption(payload['data']);
              //plotPieOverallConsumption(payload['data']);
              break;
      }
    }
}
  
  
function plotHistory(data_json)
{
    //zrobienie wykresu historii danych, jako wejście słownik:
//{'variable':nazwa_wartości,'data':{time:value...,time:value}}
    
    
    console.log('w funkcji');
    
    var y_data=[];
    let keys=Object.keys(data_json['data'])
    
    for (let k in keys)
    {
        //x_data.push(k);
        console.log(k);
        y_data.push(data_json['data'][keys[k]]);
    }

    console.log(keys);
    console.log(y_data);

    var data = [{

    x: keys,
    y: y_data,
    mode: 'lines',
    line: {color: '#80CAF6'}

    }]

    var layout= {xaxis:{title:'Czas'},yaxis:{title:'Moc [kW]'},title:'Historia zużycia energii',margin:{l:50,r:0,b:40,t:40}}

//wykres mocy chwilowej
    Plotly.newPlot('plot_history', data,layout,{displayModeBar:false});
}

//MQTT---------------------------------------------------------------------------------------
//create uuid
var uuid_num=uuid();

// Create a client instance

const BROKER_IP='192.168.1.10' 
const PORT=9001

client = new Paho.MQTT.Client(BROKER_IP, PORT, "web"+uuid_num);

// set callback handlers
//client.onConnectionLost = onConnectionLost;
client.onMessageArrived = onMessageArrived;


// connect the client
let options={
    cleanSession:false,
    reconnect:true,
    onSuccess:onConnect
}
client.connect(options);

//utworzenie wykresu mocy chwilowej
var time = new Date();

var data = [{

   x: [time],
   y: [0.0],
   mode: 'lines',
   line: {color: '#80CAF6'}

}]

var layout= {xaxis:{title:'Czas'},yaxis:{title:'Moc [kW]'},margin:{l:50,r:0,b:40,t:0}}

//wykres mocy chwilowej
Plotly.newPlot('plot', data,layout,{displayModeBar:false});
//wykres temperatury bojlera
//layout= {xaxis:{title:'Czas'},yaxis:{title:'Temperatura [°C]'},margin:{l:50,r:0,b:40,t:0}}
//Plotly.newPlot('plot_temp', data,layout,{displayModeBar:false});

//set default date and time in fields
let tfdate_from=document.getElementById("date_from");
let tfdate_to=document.getElementById("date_to");
let tftime_from=document.getElementById("time_from");
let tftime_to=document.getElementById("time_to");

let tmp_date=new Date();
let tmp_str_date=toISO(tmp_date);

tfdate_from.value=tmp_str_date.split(' ')[0];
tfdate_to.value=tmp_str_date.split(' ')[0];
tftime_from.value=tmp_str_date.split(' ')[1].slice(0,5);
tftime_to.value=tmp_str_date.split(' ')[1].slice(0,5);