
var sample_data={'2023-01-19':{'T1':11.7,'T2':10.3,'T3':21.3},
'2023-01-20':{'T1':21.7,'T2':20.3,'T3':31.3},
'2023-01-21':{'T1':37.7,'T2':27.3,'T3':37.3},
'2023-01-22':{'T1':11.7,'T2':10.3,'T3':21.3},
'2023-01-23':{'T1':21.7,'T2':20.3,'T3':31.3},
'2023-01-24':{'T1':37.7,'T2':27.3,'T3':37.3},
'2023-01-25':{'T1':11.7,'T2':10.3,'T3':21.3},
'2023-01-26':{'T1':21.7,'T2':20.3,'T3':31.3},
'2023-01-27':{'T1':37.7,'T2':27.3,'T3':37.3},
'2023-01-28':{'T1':11.7,'T2':10.3,'T3':21.3},
'2023-01-29':{'T1':21.7,'T2':20.3,'T3':31.3},
'2023-01-30':{'T1':37.7,'T2':27.3,'T3':37.3},
'2023-01-31':{'T1':11.7,'T2':10.3,'T3':21.3},
'2023-02-02':{'T1':21.7,'T2':20.3,'T3':31.3},
'2023-02-03':{'T1':37.7,'T2':27.3,'T3':37.3}
}

def_colors=[
    '#1f77b4',  // muted blue
    '#ff7f0e',  // safety orange
    '#2ca02c',  // cooked asparagus green
    '#d62728',  // brick red
    '#9467bd',  // muted purple
    '#8c564b',  // chestnut brown
    '#e377c2',  // raspberry yogurt pink
    '#7f7f7f',  // middle gray
    '#bcbd22',  // curry yellow-green
    '#17becf'   // blue-teal
]

//generowanie umikalnego identyfikatora
function uuid() {
  return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
  );
}

//ustawienie odebranych danych na stronie - moc chwilowa
function set_power(dane) {
    
    
    pole=document.getElementById("power_field");
    pole.innerHTML=String(dane['value'])+" kW";

    let date=new Date(dane['time']);

    Plotly.extendTraces('plot',{x:[[date]],y:[[dane['value']]]},[0]);
    //Plotly.update('plot',{value: parseFloat(data_spl[0])},{});
    
}

//ustawienie odebranych danych na stronie - temperatura wody
function set_temp_water(dane) {
    //let data_spl=dane.split(';');
    
    pole=document.getElementById("temp_water_field");
    pole.innerHTML=String(dane['value'].toFixed(1))+" °C";
    
    //let date=new Date(data_spl[1]);

    //Plotly.extendTraces('plot_temp',{x:[[date]],y:[[parseFloat(data_spl[0])]]},[0]);
    
}

//ustawienie odebranych danych na stronie - temperatura na zewnątrz
function set_temp_outside(dane) {
    //let data_spl=dane.split(';');
    
    pole=document.getElementById("temp_outside_field");
    pole.innerHTML=String(dane['value'].toFixed(1))+" °C";
    
    //let date=new Date(data_spl[1]);

    //Plotly.extendTraces('plot_temp',{x:[[date]],y:[[parseFloat(data_spl[0])]]},[0]);
    
}


//ustawienie odebranych danych na stronie - ciśnienie atmosferyczne
function set_pressure_outside(dane) {
    //let data_spl=dane.split(';');
    
    pole=document.getElementById("pressure_outside_field");
    pole.innerHTML=String((dane['value']/100).toFixed(1))+" hPa";
    
    //let date=new Date(data_spl[1]);

    //Plotly.extendTraces('plot_temp',{x:[[date]],y:[[parseFloat(data_spl[0])]]},[0]);
    
}

//zmieniła się wartośc daty w polu input date_from
function date_from_changed() {
    localStorage.setItem('date_from',date_from_field.value);
    //pole daty "do" nie może byćmniejsze niż "od"
    date_to_field.min=date_from_field.value;
    if (date_to_field.value<date_from_field.value) {
        date_to_field.value=date_from_field.value;
        date_to_changed();
    }
    //plot_request();
}

//zmieniła się wartośc daty w polu input date_to
function date_to_changed(){
    localStorage.setItem('date_to',date_to_field.value);
    //plot_request();
}

//wygeneruj wykresy - funkcja z eventu, wyślij żądania przez mqtt do storage
function generate_plots(){
    client.publish('storage/control',JSON.stringify({'command':'get_data','type':'day_consumption','date_from':date_from_field.value,'date_to':date_to_field.value,'answer_to':uuid_num}));
    client.publish('storage/control',JSON.stringify({'command':'get_data','type':'day_cost','date_from':date_from_field.value,'date_to':date_to_field.value,'answer_to':uuid_num}))
}



//wyszukanie odpowiednich pól
let date_from_field = document.getElementById("date_from");
let date_to_field = document.getElementById("date_to");


//odczytanie ostatnich dat
let date_from = localStorage.getItem('date_from');
let date_to = localStorage.getItem('date_to');

if ((date_from != null) && (date_to != null))
{
	date_from_field.value=date_from;
    date_to_field.value=date_to;
}

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




// called when the client connects
function onConnect() {
  // Once a connection has been made, make a subscription and send a message.
  console.log("onConnect");
  client.subscribe("World");
  client.subscribe('meter/data/power_mom');
  client.subscribe('mcp/data/temp_water');
  client.subscribe('mcp/data/temp_outside');
  client.subscribe('mcp/data/pressure');
  client.subscribe('storage/data/web/'+uuid_num)
  message = new Paho.MQTT.Message("Hello");
  message.destinationName = "World";
  client.send(message);
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
  else if (message.destinationName=='mcp/data/temp_water') {
    set_temp_water(JSON.parse(message.payloadString))
  }
  else if (message.destinationName=='mcp/data/temp_outside') {
    set_temp_outside(JSON.parse(message.payloadString))
  }
  else if (message.destinationName=='mcp/data/pressure') {
    set_pressure_outside(JSON.parse(message.payloadString))
  }
  else if (message.destinationName=='storage/data/web/'+uuid_num)
  {
    //got data for plot
    let payload = JSON.parse(message.payloadString)

    //what kind of plot have to generate
    switch (payload['data_type'])
    {
        case 'day_consumption':
            plotBarDayConsumption(payload['data']);
        	plotPieOverallConsumption(payload['data']);
            break;
        case 'day_cost':
            dayCostTable(payload['data'])


    }
  }
}

//client.subscribe('meter/data/power_mom');
console.log('tutaj');


function plotBarDayConsumption(data) {
//zrobienie wykresu zużycia w strefach, bar graph, jako wejście słownik:
//{'data1':{'T1':fff,'T2':fff,'T3':fff},'data2':{'T1':fff,'T2':fff,'T3':fff}...}

    let T1=[];
    let T2=[];
    let T3=[];
    let sum=[];
    //console.log('w funkcji');

    let keys=Object.keys(data)
    for (let k in keys)
    {
        //console.log(keys[k])
        T1.push(data[keys[k]]['T1']);
        T2.push(data[keys[k]]['T2']);
        T3.push(data[keys[k]]['T3']);
        sum.push((data[keys[k]]['T1']+data[keys[k]]['T2']+data[keys[k]]['T3']).toFixed(2));
    }

    var trace1={x:Object.keys(data),y:T1,name:'T1',type:'bar',marker:{opacity:0.8}};
    var trace2={x:Object.keys(data),y:T2,name:'T2',type:'bar',marker:{opacity:0.8}};
    var trace3={x:Object.keys(data),y:T3,name:'T3',type:'bar',text:sum,textposition:'outside',marker:{opacity:0.8}};

    var dane=[trace1,trace2,trace3]

    var layout={title:'Zużycie energii w poszczególnych dniach',barmode:'stack',xaxis: {tickangle:-90,title:'Dzień',legend:{traceorder:"normal"}},
                yaxis:{title:'Zużycie [kWh]'}}

    Plotly.newPlot('plot_bar',dane,layout)
}

function plotPieOverallConsumption(data)
{
    //zrobienie wykresu zużycia w taryfach, pie graph, jako wejście słownik:
//{'data1':{'T1':fff,'T2':fff,'T3':fff},'data2':{'T1':fff,'T2':fff,'T3':fff}...}

    let sum_pie=[0,0,0];
    

    let keys=Object.keys(data)
    for (let k in keys)
    {
        //console.log(keys[k])
        sum_pie[0]+=data[keys[k]]['T1'];
        sum_pie[1]+=data[keys[k]]['T2'];
        sum_pie[2]+=data[keys[k]]['T3'];
    }

    var trace1={values:sum_pie,labels:["T1","T2","T3"],type:'pie',text:[sum_pie[0].toFixed(2)+'kWh',sum_pie[1].toFixed(2)+'kWh',sum_pie[2].toFixed(2)+'kWh'],textinfo:"percent+text",hole:0.5,textposition:"outside",marker:{colors:[def_colors[0],def_colors[1],def_colors[2]]},hoverinfo:'label+percent+text'};
    

    var dane=[trace1];

    var layout={height:400, width:500,title:'Zużycie prądu w taryfach',legend:{traceorder:"normal"}};

    Plotly.newPlot('plot_pie',dane,layout)
}

//ustawienie odebranych danych na stronie - koszt
function dayCostTable(data) {
    window.console.log(data);
    

	//sumy pomocnicze
	let T1_sum=0.0;
	let T2_sum=0.0;
	let T3_sum=0.0;
	let sum_sum=0.0;
	let sum_sumG11=0.0;
    let bufor='<table> <tr> <th style="border:1px solid black">Data</th> <th style="border:1px solid black">Strefa T1 [zł]</th> <th style="border:1px solid black">Strefa T2 [zł]</th> <th style="border:1px solid black">Strefa T3 [zł]</th> <th style="border:1px solid black">Suma kosztów [zł]</th> <th style="border:1px solid black">Suma kosztów G11 [zł]</th></tr>';
	
	
    for (var row in data)
    {
        bufor+='<tr> <td style="border:1px solid black;padding:3px">'+row+'</td>';
        bufor+='<td style="border:1px solid black;padding:3px">'+data[row]["T1"]+'</td>';
        bufor+='<td style="border:1px solid black;padding:3px">'+data[row]["T2"]+'</td>';
        bufor+='<td style="border:1px solid black;padding:3px">'+data[row]["T3"]+'</td>';
        bufor+='<td style="border:1px solid black;padding:3px">'+data[row]['sum']+'</td>';
        bufor+='<td style="border:1px solid black;padding:3px">'+data[row]['sumG11']+'</td> </tr>';
        T1_sum+=parseFloat(data[row]["T1"])
        T2_sum+=parseFloat(data[row]["T2"])
        T3_sum+=parseFloat(data[row]["T3"])
        sum_sum+=parseFloat(data[row]["sum"])
        sum_sumG11+=parseFloat(data[row]["sumG11"])
        
    }
	bufor+='<tr> <td style="border:1px solid black;padding:3px"> Łącznie </td>';
	bufor+='<td style="border:1px solid black;padding:3px">'+T1_sum.toFixed(2)+'</td>';
	bufor+='<td style="border:1px solid black;padding:3px">'+T2_sum.toFixed(2)+'</td>';
	bufor+='<td style="border:1px solid black;padding:3px">'+T3_sum.toFixed(2)+'</td>';
	bufor+='<td style="border:1px solid black;padding:3px">'+sum_sum.toFixed(2)+'</td>';
	bufor+='<td style="border:1px solid black;padding:3px">'+sum_sumG11.toFixed(2)+'</td></tr>';

    bufor+="</table>";

    document.getElementById("data_table_place").innerHTML=bufor;

}