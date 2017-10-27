$(document).ready(function(){

$('.monthlabel').click(function(){
	cpumonth();
});

$('.daylabel').click(function(){
	cpuday();
});

$('.weeklabel').click(function(){
	cpuweek();
});


$('.memmonthlabel').click(function(){
	memmonth();
});

$('.memdaylabel').click(function(){
	memday();
});

$('.memweeklabel').click(function(){
	memweek();
});


$('.readmonthlabel').click(function(){
	readmonth();
});

$('.readdaylabel').click(function(){
	readday();
});

$('.readweeklabel').click(function(){
	readweek();
});


$('.writemonthlabel').click(function(){
	writemonth();
});

$('.writedaylabel').click(function(){
	writeday();
});

$('.writeweeklabel').click(function(){
	writeweek();
});



$('.repmonthlabel').click(function(){
	repmonth();
});

$('.repdaylabel').click(function(){
	repday();
});

$('.repweeklabel').click(function(){
	repweek();
});

$('.delmonthlabel').click(function(){
	delmonth();
});

$('.deldaylabel').click(function(){
	delday();
});

$('.delweeklabel').click(function(){
	delweek();
});

$('.prweeklabel').click(function(){
	prweek();
});

$('.prmonthlabel').click(function(){
	prmonth();
});

$('.prdaylabel').click(function(){
	prday();
});

$('.psweeklabel').click(function(){
	psweek();
});

$('.psmonthlabel').click(function(){
	psmonth();
});

$('.psdaylabel').click(function(){
	psday();
});

$('#select').find('option').each(function(){
	var vall = $(this).val();

	if (vall == 'cpu') {
		$(this).text('Cpu Usage');
	}

	if (vall == 'datain') {
		$(this).text('Traffic from Clients and Data Servers - bits');
	}

	if (vall == 'dataout') {
		$(this).text('Traffic to Clients and Data Servers - bits');
	}

	if (vall == 'bytesr') {
		$(this).text('Data Read – bytes');
	}

	if (vall == 'bytesw') {
		$(this).text('Data Written – bytes');
	}

	if (vall == 'masterin') {
		$(this).text('Traffic from Master – bits');
	}

	if (vall == 'masterout') {
		$(this).text('Traffic to Master – bits');
	}

	if (vall == 'repl') {
		$(this).text('File Replication – min');
	}

	if (vall == 'create') {
		$(this).text('File Creation – min');
	}

	if (vall == 'delete') {
		$(this).text('File Deletion – min');
	}

	if (vall == 'tests') {
		$(this).text('File Test – min');
	}
});

if (typeof('#select') != 'undefined') {

	clientday();
}


var clit = $('#clitabz');
if (typeof(clit) != 'undefined') {
		if ($('#clicpu').hasClass('active')) {
			clicpu();
		}
}

$('#clicpu').click(function(){
	clicpu();
});

$('#clitraf').click(function(){
	clitraf();
});

$('#cliperf').click(function(){
	cliperf();
});

$('#clibytes').click(function(){
	clibytes();
});





function cpumonth() {
		var half = $('#csvurl').text();
		var thisip = document.domain;
		var url = 'http://'+thisip+':9425/'+half;
		$('#cpu-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
		function doRender(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    var len = lengther-1;
		    for (i=len; i>0; i--) {
		    	

		    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	var secondval = data[i][2];
			    	
			    	if (typeof(secondval) != 'undefined') {
			    	
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							up: secondval
						});
					}
		    	
		    	
		    }
		    
		    $('#cpu-chart-area').html('');

		    Morris.Area({
			element: 'cpu-chart-area',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['m%'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData(url, callBack) {
		    Papa.parse(url, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData(url, doRender);

}




function clientday() {
	$('#clientshow').html('<p align="center" class="preloader preloaderalign"><img src="../preloader.gif"/></p>');
	var half = $('#csvurl').text();
	var thisip = document.domain;
	var url = 'http://'+thisip+':9425/'+half;
	
		function doRender(data) {
			var optiontext = $('#select option:selected').text();
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

					/*var day = myDate.getDay();
					var month = myDate.getMonth();
					var year = myDate.getYear();

					var date = month+'/'+day+'/'+year;*/
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}
			    	
			    	if ( (optiontext == 'Traffic from Clients and Data Servers - bits') || (optiontext == 'Data Read – bytes') || (optiontext == 'Traffic to Master – bits') || (optiontext == 'File Creation – min') || (optiontext == 'File Test – min')) {

			    		if (min == '49') {
							hour = hour+1;
							min = '00';
						}

						if (min == '19') {
							min = '30';
						}
			    	}
			    	
			    	
			    	if ( ( (min == '00') || (min == '30')) && hour.length != 3) {
			    	/*if (min != '00') {
			    		min = '00';
			    	}*/

			    	

			  
			    	timeframe = hour+':'+min; 

			    	
			    	
			    	if (optiontext == 'Cpu Usage') {
			    	
			    		firstval = firstval/450;
			    		secondval = secondval/450;
			    		firstval = Number((firstval).toFixed(2));
			    		secondval = Number((secondval).toFixed(2));
			    	}

			    	if (optiontext == 'Cpu Usage') {
			    		if (firstval == '') {firstval = 0}
			    		if (secondval == '') {secondval = 0}
				    	rendervar.push({
							period: timeframe,
							dl: firstval,
							up: secondval
						});
					} else {
						if (firstval == '') {firstval = 0}
						rendervar.push({
							period: timeframe,
							up: firstval
							
						});
					}

					
		    	}
		    	
		    }

		    
		    var label = '';


			if (optiontext == 'Cpu Usage') {
				label = 'm%';
			}

			if (optiontext == 'Traffic from Clients and Data Servers - bits') {
				label = 'bits';
			}

			if (optiontext == 'Traffic to Clients and Data Servers - bits') {
				label = 'bits';
			}

			if (optiontext == 'Data Read – bytes') {
				label = 'bytes';
			}

			if (optiontext == 'Data Written – bytes') {
				label = 'bytes';
			}

			if (optiontext == 'Traffic from Master – bits') {
				label = 'bits';
			}
			if (optiontext == 'Traffic to Master – bits') {
				label = 'bits';
			}
			if (optiontext == 'File Replication – min') {
				label = 'min';
			}
			if (optiontext == 'File Creation – min') {
				label = 'min';
			}
			if (optiontext == 'File Deletion – min') {
				label = 'min';
			}
			if (optiontext == 'File Test – min') {
				label = 'min';
			}

			
		    
		    $('#clientshow').html('');

		    Morris.Area({
			element: 'clientshow',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: [label],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData(url, callBack) {
		    Papa.parse(url, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData(url, doRender);
}

var chartpage = $('#cpu-chart-area');

if (typeof(chartpage) != 'undefined') {
	var thisip = document.domain;
	//CPU +++++++++++++++++++++++++++++++++++++:
		cpuday();

	// END CPU ++++++++++++++++++++++++++++++++++++
	

}

$('.tabelo li').click(function(e){
	e.preventDefault();
	$('.tabelo').find('.active').toggleClass('active');
	$(this).addClass('active');
	var hrefo = $(this).find('a').attr('href');
	
	$('.tabelocont').find('.active').toggleClass('active');
	$('.tabelocont').find('.in').toggleClass('in');
	$(hrefo).addClass('in');
	$(hrefo).addClass('active');
	var name = $(this).find('a').text();
	var thisip = document.domain;

	//CPU +++++++++++++++++++++++++++++++++++++:
	if (name == 'CPU') {
		$('#cpu-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
		
		cpuday();
	}
	// END CPU ++++++++++++++++++++++++++++++++++++

	// MEMORY +++++++++++++++++++++++++++++++++++++

	if (name == 'Memory') {
		memday();
	}

	// END MEMORY +++++++++++++++++++++++++++++++++


	// DELETION +++++++++++++++++++++++++++++++++++++

	if (name == 'Deletion') {
		delday();
	}

	

	// END DELETION +++++++++++++++++++++++++++++++++

	// REPLICATION +++++++++++++++++++++++++++++++++++++

	if (name == 'Replication') {
		repday();
	}

	// END REPLICATION +++++++++++++++++++++++++++++++++

	// READ +++++++++++++++++++++++++++++++++++++


	if (name == 'Read') {
		readday();	
	}


	// END READ +++++++++++++++++++++++++++++++++

	// WRITE +++++++++++++++++++++++++++++++++++++


	if (name == 'Write') {
		writeday();
	}

	// END WRITE +++++++++++++++++++++++++++++++++

	// PACKETS RECEIVED +++++++++++++++++++++++++++++++++++++

	if (name == 'Packets Received') {
	
		prday();
	}

	// END PACKETS RECEIVED +++++++++++++++++++++++++++++++++

	// PACKETS SENT +++++++++++++++++++++++++++++++++++++

	if (name == 'Packets Sent') {
		psday();
	}


	// END PACKETS SENT +++++++++++++++++++++++++++++++++

});

$('.filepanele').each(function(e){
	var textf = '';
	var iconf = '';

	if (e == 0) {
		textf = 'All Files';
		iconf = 'fa-file-o';

		$(this).find('.bgcolor').addClass('bg-info');
		$(this).find('.icof').addClass(iconf);
		$(this).find('.textf').text(textf);
		
	}

	if (e == 1) {
		textf = 'Health Files';
		iconf = 'fa-file-o';

		$(this).find('.bgcolor').addClass('bg-success');
		$(this).find('.icof').addClass(iconf);
		$(this).find('.textf').text(textf);
		
	}

	if (e == 2) {
		textf = 'Endangered Files';
		iconf = 'fa-file-o';

		$(this).find('.bgcolor').addClass('bg-warning');
		$(this).find('.icof').addClass(iconf);
		$(this).find('.textf').text(textf);
		
	}

	if (e == 3) {
		textf = 'Missing Files';
		iconf = 'fa-file-o';

		$(this).find('.bgcolor').addClass('bg-danger');
		$(this).find('.icof').addClass(iconf);
		$(this).find('.textf').text(textf);
		
	}
});

$('.MENUZ').find('a').each(function(){
	var text = $(this).text();
	if (text == 'Config') {
		$(this).closest('li').hide();
	}

	if (text == 'Mounts') {
		$(this).closest('li').hide();
	}

	if (text == 'Operations') {
		$(this).closest('li').hide();
	}

	if (text == 'Help') {
		$(this).closest('li').hide();
	}
});

$('.MENUZ').find('.US').addClass('active');

$('.vdiskstat').each(function(){
	var stat = $(this).text();
	var res = '<div class="label label-table label-primary">'+stat+'</div>';

	if (stat == 'ok') {
		res = '<div class="label label-table label-success">'+stat+'</div>';
	} 

	if (stat == 'damaged') {
		res = '<div class="label label-table label-danger">'+stat+'</div>';
	} 

	$(this).html(res);

});

$('.statusstater').each(function(){
	var stat = $(this).text();
	$(this).addClass('label label-table label-primary');

	if (stat == 'running') {
		$(this).addClass('label-success');
	}

	if (stat == 'stopped') {
		$(this).addClass('label-danger');
	}
});


var valfirst = $('#files-line').text();

if (valfirst == 'No data for display') {
							$('#files-line').text('');
							$('#files-line-del').text('');
			var files_data = new Array();
			var files_data_old = new Array();
			$('.firstfiles').each(function(index){
				var val = $(this).text();

				
				if (val == '-') {
					val = 0;
				}
				val = parseInt(val);
				if (index <= 10) {
					files_data.push({"elapsed": index, "value": val});
				} else {
					index = index-11;
					files_data_old.push({"elapsed": index, "value": val});
				}
			});

			
							
							Morris.Line({
								element: 'files-line',
								data: files_data,
								xkey: 'elapsed',
								ykeys: ['value'],
								ymin: 0,
								labels: ['value'],
								gridEnabled: false,
								gridLineColor: 'transparent',
								lineColors: ['#045d97'],
								lineWidth: 2,
								parseTime: false,
								resize:true,
								hideHover: 'auto'
							});

							Morris.Line({
								element: 'files-line-del',
								data: files_data_old,
								xkey: 'elapsed',
								ymin: 0,
								ykeys: ['value'],
								labels: ['value'],
								gridEnabled: false,
								gridLineColor: 'transparent',
								lineColors: ['#045d97'],
								lineWidth: 2,
								parseTime: false,
								resize:true,
								hideHover: 'auto'
							});
						}



var availsp = $('#availspacehddo').text();
var totalsp = $('#totalspacehddo').text();

	

if (typeof(availsp) != '') {

$('.charter').each(function(){
	var obj = $(this);
	$(obj).easyPieChart({
		barColor :'#68b828',
		scaleColor: false,
		trackColor : '#eee',
		lineCap : 'round',
		lineWidth :8,
		onStep: function(from, to, percent) {
			$(this.el).find('.pie-value').text(Math.round(percent) + '%');
		}
	});
});
	
	
	
	var valuz = availsp.substr(availsp.length - 3);

	var valuze = '';
	if (valuz == 'GiB') {
		valuze = ' (GB)';
	}

	if (valuz == 'MiB') {
		valuze = ' (MB)';
	}

	$('#valuz').text(valuze);

	availsp = parseInt(availsp);
	totalsp = parseInt(totalsp);
    
	var usedsp = totalsp - availsp;

	
	Morris.Donut({
				element: 'ramspace',
				data: [
					{label: "Free", value: availsp},
					{label: "Used", value: usedsp}
					
				],
				colors: [
					'#a6c600',
					'#177bbb'
				],
				resize:true
			});


	// MEMORY:

	$('#valuze').text(valuze);


	var availsm = $('#memusage').text();
	var totalsm = $('#memtotal').text();
	
	
	var valuz = availsm.substr(availsm.length - 3);

	var valuze = '';
	if (valuz == 'GiB') {
		valuze = ' (GB)';
	}

	if (valuz == 'MiB') {
		valuze = ' (MB)';
	}

	$('#valuze').text(valuze);

	availsm = parseInt(availsm);
	totalsm = parseInt(totalsm);
    
	var usedsm = totalsm - availsm;


		Morris.Donut({
				element: 'storagespace',
				data: [
					{label: "Free", value: availsm},
					{label: "Used", value: usedsm}
					
				],
				colors: [
					'#a6c600',
					'#177bbb'
				],
				resize:true
			});

	$('.tablejsmove').each(function(){
		var obj = $(this).html();
		$('#container').append(obj);
		$(this).remove();
	});

}



function cpuday() {
		var url = 'http://'+thisip+':9425/chart.cgi?host=127.0.0.1&port=9421&id=91000';
		$('#cpu-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
		function doRender(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

					/*var day = myDate.getDay();
					var month = myDate.getMonth();
					var year = myDate.getYear();

					var date = month+'/'+day+'/'+year;*/
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}
			    	
			    	if ( (min == '00') || (min == '30')) {
			    	/*if (min != '00') {
			    		min = '00';
			    	}*/

			    	

			  
			    	timeframe = hour+':'+min; 

			    	
			    	
			    	firstval = firstval/450;
			    	secondval = secondval/450;

			    	firstval = Number((firstval).toFixed(2));
			    	secondval = Number((secondval).toFixed(2));

			    	rendervar.push({
						period: timeframe,
						dl: firstval,
						up: secondval
					});
		    	}
		    	
		    }
		    
		    $('#cpu-chart-area').html('');

		    Morris.Area({
			element: 'cpu-chart-area',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['m%'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData(url, callBack) {
		    Papa.parse(url, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData(url, doRender);
}


function cpumonth() {
		var url = 'http://'+thisip+':9425/csvapi.cgi?period=month&action=cpu';
		$('#cpu-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
		function doRender(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    var len = lengther-1;
		    for (i=len; i>0; i--) {
		    	

		    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	var secondval = data[i][2];
			    	
			    	if (typeof(secondval) != 'undefined') {
			    	
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							up: secondval
						});
					}
		    	
		    	
		    }
		    
		    $('#cpu-chart-area').html('');

		    Morris.Area({
			element: 'cpu-chart-area',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['m%'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData(url, callBack) {
		    Papa.parse(url, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData(url, doRender);
}


function cpuweek() {
		var url = 'http://'+thisip+':9425/csvapi.cgi?period=week&action=cpu';
		$('#cpu-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
		function doRender(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    var len = lengther-1;
		    for (i=len; i>0; i--) {
		    	

		    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	var secondval = data[i][2];
			    	
			    	if (typeof(secondval) != 'undefined') {
			    	
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							up: secondval
						});
					}
		    	
		    	
		    }
		    
		    $('#cpu-chart-area').html('');

		    Morris.Area({
			element: 'cpu-chart-area',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['m%'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData(url, callBack) {
		    Papa.parse(url, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData(url, doRender);
}


function memday() {

	$('#memory-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			

	var urlmem = 'http://'+thisip+':9425/chart.cgi?host=127.0.0.1&port=9421&id=90200';

	function doRendermem(data) {
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;

	    for (i=1; i<lengther; i++) {
	    	

	    		var timeframe = data[i][0];

		    	var timeframe = timeframe*1000-2460000;
			    var dt=eval(timeframe);
				var myDate = new Date(dt);
				var date = myDate.toLocaleString();

				var min = myDate.getUTCMinutes();
				var hour = myDate.getUTCHours();

			
					var ndate = date.split(',');
					date = ndate[0];
					//$('.todate').text(date);
				



				min = min.toString();
				hour = hour.toString();

			

		    	var firstval = data[i][1];
		    	if (firstval == '') {
		    		firstval = 0;
		    	}


		    	if (typeof(firstval) != 'undefined') {
		    		firstval = firstval/1024/1024;
		    		firstval = Number((firstval).toFixed(2));
			    } else {
			    	firstval = 0;
			    }

		    	if (hour.length < 2) {
		    		hour = '0'+hour;
		    	}

		    	if (min.length < 2) {
		    		min = '0'+min;
		    	}
		    	
		    	timeframe = hour+':'+min; 
		    	if ( (min == '00') || ( min == '30') ) {
		    		rendervar.push({
						period: timeframe,
						dl: firstval,
					});
		    	}

		    	
	    	
	    	
	    }
	    
	    $('#memory-chart-area').html('');

	    Morris.Area({
		element: 'memory-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['MB'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatamem(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatamem(urlmem, doRendermem);

}


function memweek() {

	$('#memory-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			

	var urlmem = 'http://'+thisip+':9425/csvapi.cgi?period=week&action=memory';

	function doRendermem(data) {
	
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;

	    for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		firstval = firstval/1024/1024;
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	    
	    $('#memory-chart-area').html('');

	    Morris.Area({
		element: 'memory-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['MB'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatamem(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatamem(urlmem, doRendermem);

}


function memmonth() {

	$('#memory-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			

	var urlmem = 'http://'+thisip+':9425/csvapi.cgi?period=month&action=memory';

	function doRendermem(data) {
		
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;

	   	for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		firstval = firstval/1024/1024;
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	    	
	    	
	    
	    
	    $('#memory-chart-area').html('');

	    Morris.Area({
		element: 'memory-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['MB'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatamem(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatamem(urlmem, doRendermem);

}


function delday() {
	$('#deletion-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			

	var urldele = 'http://'+thisip+':9425/chart.cgi?host=127.0.0.1&port=9421&id=90020';

	function doRenderdele (data) {
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;

	    for (i=1; i<lengther; i++) {
	    	

	    		var timeframe = data[i][0];

		    	var timeframe = timeframe*1000-2460000;
			    	var dt=eval(timeframe);
				var myDate = new Date(dt);
				var date = myDate.toLocaleString();

				var min = myDate.getUTCMinutes();
				var hour = myDate.getUTCHours();

				
					var ndate = date.split(',');
					date = ndate[0];
					//$('.todate').text(date);
				



				min = min.toString();
				hour = hour.toString();

				

		    	var firstval = data[i][1];
		    	if (firstval == '') {
		    		firstval = 0;
		    	}

		    	if (typeof(firstval) != 'undefined') {
		    		firstval = Number((firstval).toFixed(2));
			    } else {
			    	firstval = 0;
			    }
		    	//firstval = firstval/10;
		    	
		    	if (hour.length < 2) {
		    		hour = '0'+hour;
		    	}

		    	if (min.length < 2) {
		    		min = '0'+min;
		    	}
		    	
		    	timeframe = hour+':'+min; 

		    	if ( (min == '00') || (min == '30')) {
			    	rendervar.push({
						period: timeframe,
						dl: firstval,
					});
	    		}
	    	
	    }
	    
	    $('#deletion-chart-area').html('');

	    Morris.Area({
		element: 'deletion-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['files'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatadele(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatadele(urldele, doRenderdele);
}

function delweek() {
		$('#deletion-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			

	var urldele = 'http://'+thisip+':9425/csvapi.cgi?period=week&action=deletion';

	function doRenderdele (data) {
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;
	
		for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	    
	    $('#deletion-chart-area').html('');

	    Morris.Area({
		element: 'deletion-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['files'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatadele(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatadele(urldele, doRenderdele);
}



function delmonth() {
		$('#deletion-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			

	var urldele = 'http://'+thisip+':9425/csvapi.cgi?period=month&action=deletion';

	function doRenderdele (data) {
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;
	   
	    for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	    
	    $('#deletion-chart-area').html('');

	    Morris.Area({
		element: 'deletion-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['files'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatadele(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatadele(urldele, doRenderdele);
}

function repday() {
	$('#replication-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlrepl = 'http://'+thisip+':9425/chart.cgi?host=127.0.0.1&port=9421&id=90030';

	function doRenderrepl (data) {
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;

	    for (i=1; i<lengther; i++) {
	    	

	    		var timeframe = data[i][0];

		    	var timeframe = timeframe*1000-2460000;
			    	var dt=eval(timeframe);
				var myDate = new Date(dt);
				var date = myDate.toLocaleString();

				var min = myDate.getUTCMinutes();
				var hour = myDate.getUTCHours();

				
					var ndate = date.split(',');
					date = ndate[0];
					//$('.todate').text(date);





				min = min.toString();
				hour = hour.toString();

			

		    	var firstval = data[i][1];
		    	if (firstval == '') {
		    		firstval = 0;
		    	}

		    	if (typeof(firstval) != 'undefined') {
		    		firstval = Number((firstval).toFixed(2));
		    	} else {
			    	firstval = 0;
			    }

		    	//firstval = firstval/10;
		    	if (hour.length < 2) {
		    		hour = '0'+hour;
		    	}

		    	if (min.length < 2) {
		    		min = '0'+min;
		    	}

		    		
			    		if (min == '49') {
							hour = hour+1;
							min = '00';
						}

						if (min == '19') {
							min = '30';
						}
			    	
		    	
		    	timeframe = hour+':'+min; 

		    	if ( (min == '00') || (min == '30') ){
		    	rendervar.push({
					period: timeframe,
					dl: firstval,
				});
	    		}
	    	
	    }
	    
	   
	    $('#replication-chart-area').html('');

	    Morris.Area({
		element: 'replication-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['files'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatarepl(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatarepl(urlrepl, doRenderrepl);

}


function repweek() {
	$('#replication-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlrepl = 'http://'+thisip+':9425/csvapi.cgi?period=week&action=replication';

	function doRenderrepl (data) {
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;

	    		for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	   
	    $('#replication-chart-area').html('');

	    Morris.Area({
		element: 'replication-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['files'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatarepl(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatarepl(urlrepl, doRenderrepl);
}

function repmonth() {
	$('#replication-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlrepl = 'http://'+thisip+':9425/csvapi.cgi?period=month&action=replication';

	function doRenderrepl (data) {
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;

	    		for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	   
	    $('#replication-chart-area').html('');

	    Morris.Area({
		element: 'replication-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['files'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatarepl(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatarepl(urlrepl, doRenderrepl);
}

function readmonth() {
	$('#read-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlread = 'http://'+thisip+':9425/csvapi.cgi?period=month&action=read';

	function doRenderread (data) {
	    //Data is usable here
	    var rendervar = [];
	   

	    var lengther = data.length;

	    	for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	   
	    $('#read-chart-area').html('');
	    
	    Morris.Area({
		element: 'read-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['read'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDataread(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDataread(urlread, doRenderread);
}

function readweek() {
	$('#read-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlread = 'http://'+thisip+':9425/csvapi.cgi?period=week&action=read';

	function doRenderread (data) {
	    //Data is usable here
	    var rendervar = [];
	   

	    var lengther = data.length;

	    	for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	   
	    $('#read-chart-area').html('');
	    
	    Morris.Area({
		element: 'read-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['read'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDataread(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDataread(urlread, doRenderread);
}

function readday() {
	$('#read-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlread = 'http://'+thisip+':9425/chart.cgi?host=127.0.0.1&port=9421&id=90040';

	function doRenderread (data) {
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;

	    for (i=1; i<lengther; i++) {
	    	j = j + 1;

	    	//if (j == 10) {
	    		j = 0;

	    		var timeframe = data[i][0];

		    	var timeframe = timeframe*1000-2460000;
			    	var dt=eval(timeframe);
				var myDate = new Date(dt);
				var date = myDate.toLocaleString();

				var min = myDate.getUTCMinutes();
				var hour = myDate.getUTCHours();

				
					var ndate = date.split(',');
					date = ndate[0];
					//$('.todate').text(date);
				



				min = min.toString();
				hour = hour.toString();

			
		    	var firstval = data[i][1];
		    	if (firstval == '') {
		    		firstval = 0;
		    	}
		    	
		    	if (typeof(firstval) != 'undefined') {
		    		firstval = Number((firstval).toFixed(2));
		    	} else {
			    	firstval = 0;
			    }
		    	//firstval = firstval/10;
		    	if (hour.length < 2) {
		    		hour = '0'+hour;
		    	}

		    	if (min.length < 2) {
		    		min = '0'+min;
		    	}
		    	
		    	timeframe = hour+':'+min; 

		    	if ( (min == '00') || (min == '30')) {
			    	rendervar.push({
						period: timeframe,
						dl: firstval,
					});
				}
	    	//}
	    	
	    }
	    
	    $('#read-chart-area').html('');

	    Morris.Area({
		element: 'read-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['read'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDataread(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDataread(urlread, doRenderread);

	

}

function writeday() {
	$('#write-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlwrite = 'http://'+thisip+':9425/chart.cgi?host=127.0.0.1&port=9421&id=90050';

	function doRenderwrite (data) {
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;

	    for (i=1; i<lengther; i++) {
	    	

	    		var timeframe = data[i][0];

		    	var timeframe = timeframe*1000-2460000;
			    	var dt=eval(timeframe);
				var myDate = new Date(dt);
				var date = myDate.toLocaleString();

				var min = myDate.getUTCMinutes();
				var hour = myDate.getUTCHours();
				
				
					var ndate = date.split(',');
					date = ndate[0];
					//$('.todate').text(date);
				



				min = min.toString();
				hour = hour.toString();

			

		    	var firstval = data[i][1];
		    	if (firstval == '') {
		    		firstval = 0;
		    	}
		    	
		    	if (typeof(firstval) != 'undefined') {
		    		firstval = Number((firstval).toFixed(2));
		    	} else {
			    	firstval = 0;
			    }

		    	//firstval = firstval/10;
		    	if (hour.length < 2) {
		    		hour = '0'+hour;
		    	}

		    	if (min.length < 2) {
		    		min = '0'+min;
		    	}
		    		
			    		if (min == '49') {
							hour = hour+1;
							min = '00';
						}

						if (min == '19') {
							min = '30';
						}
			    	

		    	timeframe = hour+':'+min; 

		    	if ( (min == '00') || (min == '30')) {
			    	rendervar.push({
						period: timeframe,
						dl: firstval,
					});
				}
	    	//}
	    	
	    }
	    
	    $('#write-chart-area').html('');

	    Morris.Area({
		element: 'write-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['write'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatawrite(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatawrite(urlwrite, doRenderwrite);

}


function writemonth() {
	$('#write-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlwrite = 'http://'+thisip+':9425/csvapi.cgi?period=month&action=write';

	function doRenderwrite (data) {
	    //Data is usable here
	    var rendervar = [];
	   

	    var lengther = data.length;

	    	for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	   
	    $('#write-chart-area').html('');
	    
	    Morris.Area({
		element: 'write-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['write'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatawrite(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatawrite(urlwrite, doRenderwrite);
}

function writeweek() {
	$('#write-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlwrite = 'http://'+thisip+':9425/csvapi.cgi?period=week&action=write';

	function doRenderwrite (data) {
	    //Data is usable here
	    var rendervar = [];
	   

	    var lengther = data.length;

	    	for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	   
	    $('#write-chart-area').html('');
	    
	    Morris.Area({
		element: 'write-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['write'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatawrite(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatawrite(urlwrite, doRenderwrite);
}

function prday() {
		$('#pr-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlpr = 'http://'+thisip+':9425/chart.cgi?host=127.0.0.1&port=9421&id=90060';

	function doRenderpr (data) {
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;

	    for (i=1; i<lengther; i++) {
	    
	    		var timeframe = data[i][0];

		    	var dt=eval(timeframe*1000-2460000);
				var myDate = new Date(dt);
				var date = myDate.toLocaleString();

				var min = myDate.getUTCMinutes();
				var hour = myDate.getUTCHours();

				
					var ndate = date.split(',');
					date = ndate[0];
					//$('.todate').text(date);
				



				min = min.toString();
				hour = hour.toString();

			

		    	var firstval = data[i][1];
		    	if (firstval == '') {
		    		firstval = 0;
		    	}
		    	
		    	if (typeof(firstval) != 'undefined') {
		    		firstval = Number((firstval).toFixed(2));
		    	} else {
			    	firstval = 0;
			    }

		    	//firstval = firstval/10;
		    	if (hour.length < 2) {
		    		hour = '0'+hour;
		    	}

		    	if (min.length < 2) {
		    		min = '0'+min;
		    	}
		    	
		    	timeframe = hour+':'+min; 

		    	if ( (min == '00') || (min == '30')) {
			    	rendervar.push({
						period: timeframe,
						dl: firstval,
					});
				}
	    	//}
	    	
	    }
	    
	    $('#pr-chart-area').html('');

	    Morris.Area({
		element: 'pr-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['Packets'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatapr(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatapr(urlpr, doRenderpr);

}

function prweek() {
	$('#pr-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlpr = 'http://'+thisip+':9425/csvapi.cgi?period=week&action=packets_received';

	function doRenderpr (data) {
	    //Data is usable here
	    var rendervar = [];
	   

	    var lengther = data.length;

	    	for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	   
	    $('#pr-chart-area').html('');
	    
	    Morris.Area({
		element: 'pr-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['Packets'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatapr(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatapr(urlpr, doRenderpr);
}


function psweek() {
	$('#ps-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlps = 'http://'+thisip+':9425/csvapi.cgi?period=week&action=packets_write';

	function doRenderps (data) {
	    //Data is usable here
	    var rendervar = [];
	   

	    var lengther = data.length;

	    	for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	   
	    $('#ps-chart-area').html('');
	    
	    Morris.Area({
		element: 'ps-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['Packets'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDataps(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDataps(urlps, doRenderps);
}

function prmonth() {
	$('#pr-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlpr = 'http://'+thisip+':9425/csvapi.cgi?period=month&action=packets_received';

	function doRenderpr (data) {
	    //Data is usable here
	    var rendervar = [];
	   

	    var lengther = data.length;

	    	for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	   
	    $('#pr-chart-area').html('');
	    
	    Morris.Area({
		element: 'pr-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['Packets'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDatapr(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDatapr(urlpr, doRenderpr);
}


function psmonth() {
	$('#ps-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlps = 'http://'+thisip+':9425/csvapi.cgi?period=month&action=packets_write';

	function doRenderps (data) {
	    //Data is usable here
	    var rendervar = [];
	   

	    var lengther = data.length;

	    	for (i=lengther; i>0; i--) {
	    	
	    	if (typeof(data[i]) != 'undefined') {
	    		var timeframe = data[i][0];
			    	var firstval = data[i][1];
			    	
			    	
			    	if (typeof(firstval) != 'undefined') {
			    	
			    		
			    		firstval = Number((firstval).toFixed(2));
			   
			    		rendervar.push({
							period: timeframe,
							dl: firstval,
							
						});
					}
		    }
	    }
	   
	    $('#ps-chart-area').html('');
	    
	    Morris.Area({
		element: 'ps-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['Packets'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDataps(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDataps(urlps, doRenderps);
}

function psday() {

	$('#ps-chart-area').html('<p align="center" class="preloader"><img src="../preloader.gif"/></p>');
			
		
	var urlps = 'http://'+thisip+':9425/chart.cgi?host=127.0.0.1&port=9421&id=90070';

	function doRenderps (data) {
	    //Data is usable here
	    var rendervar = [];
	    

	    var lengther = data.length;

	    for (i=1; i<lengther; i++) {
	    

	    		var timeframe = data[i][0];

		    	var dt=eval(timeframe*1000-2460000);
				var myDate = new Date(dt);
				var date = myDate.toLocaleString();

				var min = myDate.getUTCMinutes();
				var hour = myDate.getUTCHours();

				
					var ndate = date.split(',');
					date = ndate[0];
					//$('.todate').text(date);
				



				min = min.toString();
				hour = hour.toString();


		    	var firstval = data[i][1];
		    	if (firstval == '') {
		    		firstval = 0;
		    	}
		    	
		    	if (typeof(firstval) != 'undefined') {
		    		firstval = Number((firstval).toFixed(2));
		    	} else {
			    	firstval = 0;
			    }

		    	//firstval = firstval/10;
		    	if (hour.length < 2) {
		    		hour = '0'+hour;
		    	}

		    	if (min.length < 2) {
		    		min = '0'+min;
		    	}

		    		
			    		if (min == '49') {
							hour = hour+1;
							min = '00';
						}

						if (min == '19') {
							min = '30';
						}
			    	
		    	
		    	timeframe = hour+':'+min; 

		    	if ( (min == '00') || (min == '30') ) {
			    	rendervar.push({
						period: timeframe,
						dl: firstval,
					});
				}
	    	//}
	    	
	    }
	    
	    $('#ps-chart-area').html('');

	    Morris.Area({
		element: 'ps-chart-area',
		data: rendervar,
		gridEnabled: false,
		gridLineColor: 'transparent',
		behaveLikeLine: true,
		xkey: 'period',
		ykeys: ['dl'],
		labels: ['Packets'],
		lineColors: ['#045d97'],
		pointSize: 0,
		pointStrokeColors : ['#045d97'],
		lineWidth: 0,
		resize:true,
		hideHover: 'auto',
		fillOpacity: 0.7,
		parseTime:false
	});
	}

	function parseDataps(url, callBack) {
	    Papa.parse(url, {
	        download: true,
	        dynamicTyping: true,
	        complete: function(results) {
	            callBack(results.data);
	        }
	    });
	}

	parseDataps(urlps, doRenderps);
}

});



function clicpu() {
	chartclienterase();
	$('.preload1').show();
	$('#clientside1').show();
	$('#chart-client-1').html("");
	$('#chart-client-1').show();

	var half = $('#clichart1 a').attr('href');
		var thisip = document.domain;
		var urlclicpu = 'http://'+thisip+':9425/'+half;

		function doRendercli(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

					/*var day = myDate.getDay();
					var month = myDate.getMonth();
					var year = myDate.getYear();

					var date = month+'/'+day+'/'+year;*/
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}
			    	
			    	if ( (min == '00') || (min == '30')) {
			    	/*if (min != '00') {
			    		min = '00';
			    	}*/

			    	

			  
			    	timeframe = hour+':'+min; 

			    	
			    	
			    	firstval = firstval/450;
			    	secondval = secondval/450;

			    	firstval = Number((firstval).toFixed(2));
			    	secondval = Number((secondval).toFixed(2));

			    	rendervar.push({
						period: timeframe,
						dl: firstval,
						up: secondval
					});
		    	}
		    	
		    }
		    
		    

		    $('.preload1').hide();

		 Morris.Area({
			element: 'chart-client-1',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['m%'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData(url, callBack) {
		    Papa.parse(urlclicpu, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData(urlclicpu, doRendercli);
}

function clitraf() {
	chartclienterase();
	$('.clientside').hide();

	$('.preload2').show();
	$('#clientside2').show();
	

	$('.preload3').show();
	$('#clientside3').show();
	

	$('.preload7').show();
	$('#clientside7').show();

		$('.preload6').show();
	$('#clientside6').show();
	
	$('#chart-client-2').show();
	$('#chart-client-3').show();
	$('#chart-client-7').show();
	$('#chart-client-6').show();


		var half = $('#clichart2 a').attr('href');
		var thisip = document.domain;
		var urlcli2 = 'http://'+thisip+':9425/'+half;

		var half = $('#clichart3 a').attr('href');
		var urlcli3 = 'http://'+thisip+':9425/'+half;

		var half = $('#clichart7 a').attr('href');
		var urlcli7 = 'http://'+thisip+':9425/'+half;

		function doRendercli2(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

					/*var day = myDate.getDay();
					var month = myDate.getMonth();
					var year = myDate.getYear();

					var date = month+'/'+day+'/'+year;*/
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}

			    	if (min == '49') {
							hour = hour+1;
							min = '00';
						}

						if (min == '19') {
							min = '30';
						}
			    	

			    	if ( ((min == '00') || (min == '30')) && hour.length < 3 ) {
			    	/*if (min != '00') {
			    		min = '00';
			    	}*/

			    	

			  		
			    	timeframe = date+'-'+hour+':'+min; 
			    	

			    	//firstval = Number((firstval).toFixed(2));
			    	if (firstval == '') {
			    		firstval = 0;
			    	}

			    	rendervar.push({
						period: timeframe,
						up: firstval
					});
		    	}
		    	
		    }
		    
		  

		    $('.preload2').hide();

		 Morris.Area({
			element: 'chart-client-2',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['bits'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData2(url, callBack) {
		    Papa.parse(urlcli2, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData2(urlcli2, doRendercli2);


		function doRendercli3(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

				
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}

			    	
			    	
			    	if ( ((min == '00') || (min == '30')) && hour.length < 3 ) {
			    	

			    	

			  
			    	timeframe = hour+':'+min; 

			    	if (firstval == '') {
			    		firstval = 0;
			    	}
			    	
			    	
			    	

			    	//firstval = Number((firstval).toFixed(2));
			    

			    	rendervar.push({
						period: timeframe,
						up: firstval
					});
		    	}
		    	
		    }
		    
		  

		    $('.preload3').hide();

		 Morris.Area({
			element: 'chart-client-3',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['bits'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData3(url, callBack) {
		    Papa.parse(urlcli3, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData3(urlcli3, doRendercli3);



		function doRendercli7(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

				
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}

						if (min == '49') {
							hour = hour+1;
							min = '00';
						}

						if (min == '19') {
							min = '30';
						}
			    
			    	
			    	if ( ((min == '00') || (min == '30') ) && hour.length < 3) {
			    
			    	

			  
			    	timeframe = date+'-'+hour+':'+min; 

			    	
			    	if (firstval == '') {
			    		firstval = 0;
			    	}
			    	
			    	

			    	//firstval = Number((firstval).toFixed(2));
			    

			    	rendervar.push({
						period: timeframe,
						up: firstval
					});
		    	}
		    	
		    }
		    
		  

		    $('.preload7').hide();

		 Morris.Area({
			element: 'chart-client-7',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['bits'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData7(url, callBack) {
		    Papa.parse(urlcli7, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData7(urlcli7, doRendercli7);
	function doRendercli6(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

					/*var day = myDate.getDay();
					var month = myDate.getMonth();
					var year = myDate.getYear();

					var date = month+'/'+day+'/'+year;*/
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}

			    	

			    	if ( ((min == '00') || (min == '30')) && hour.length < 3 ) {
			    	/*if (min != '00') {
			    		min = '00';
			    	}*/

			    	

			  
			    	timeframe = hour+':'+min; 
			    	

			    	//firstval = Number((firstval).toFixed(2));
			    	if (firstval == '') {
			    		firstval = 0;
			    	}

			    	rendervar.push({
						period: timeframe,
						up: firstval
					});
		    	}
		    	
		    }
		    
		 

		    $('.preload6').hide();

		 Morris.Area({
			element: 'chart-client-6',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['bits'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData6(url, callBack) {
		    Papa.parse(url, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		var thisip = document.domain;
		var half = $('#clichart6 a').attr('href');
		var urlcli6 = 'http://'+thisip+':9425/'+half;

		parseData6(urlcli6, doRendercli6);
}




function clibytes() {
	chartclienterase();
	$('.clientside').hide();

	$('.preload4').show();
	$('#clientside4').show();
	

	$('.preload5').show();
	$('#clientside5').show();
	


	
	$('#chart-client-4').show();
	$('#chart-client-5').show();
	

		var half4 = $('#clichart4 a').attr('href');
		var thisip = document.domain;
		var urlcli4 = 'http://'+thisip+':9425/'+half4;

		var half5 = $('#clichart5 a').attr('href');
		var urlcli5 = 'http://'+thisip+':9425/'+half5;

		

		function doRendercli4(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

					/*var day = myDate.getDay();
					var month = myDate.getMonth();
					var year = myDate.getYear();

					var date = month+'/'+day+'/'+year;*/
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}

			    	if (min == '49') {
							hour = hour+1;
							min = '00';
						}

						if (min == '19') {
							min = '30';
						}
			    	

			    	if ( ((min == '00') || (min == '30')) && hour.length < 3 ) {
			    	/*if (min != '00') {
			    		min = '00';
			    	}*/

			    	

			  
			    	timeframe = date+'-'+ hour+':'+min; 
			    	console.log(timeframe);

			    	//firstval = Number((firstval).toFixed(2));
			    	if (firstval == '') {
			    		firstval = 0;
			    	}

			    	rendervar.push({
						period: timeframe,
						up: firstval
					});
		    	}
		    	
		    }
		    
		 

		    $('.preload4').hide();

		 Morris.Area({
			element: 'chart-client-4',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['bits'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData4(url, callBack) {
		    Papa.parse(url, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData4(urlcli4, doRendercli4);


			function doRendercli5(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

					/*var day = myDate.getDay();
					var month = myDate.getMonth();
					var year = myDate.getYear();

					var date = month+'/'+day+'/'+year;*/
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}

			    
			    	

			    	if ( ((min == '00') || (min == '30')) && hour.length < 3 ) {
			    	/*if (min != '00') {
			    		min = '00';
			    	}*/

			    	

			  
			    	timeframe = hour+':'+min; 
			    	

			    	//firstval = Number((firstval).toFixed(2));
			    	if (firstval == '') {
			    		firstval = 0;
			    	}

			    	rendervar.push({
						period: timeframe,
						up: firstval
					});
		    	}
		    	
		    }
		    
		

		    $('.preload5').hide();

		 Morris.Area({
			element: 'chart-client-5',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['bits'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData5(url, callBack) {
		    Papa.parse(url, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData5(urlcli5, doRendercli5);

}



function cliperf() {
	chartclienterase();
	$('.clientside').hide();

	$('.preload8').show();
	$('#clientside8').show();
	

	$('.preload9').show();
	$('#clientside9').show();
	

	$('.preload10').show();
	$('#clientside10').show();

	$('.preload11').show();
	$('#clientside11').show();
	
	$('#chart-client-8').show();
	$('#chart-client-9').show();
	$('#chart-client-10').show();
	$('#chart-client-11').show();


		var half = $('#clichart8 a').attr('href');
		var thisip = document.domain;
		var urlcli8 = 'http://'+thisip+':9425/'+half;

		var half = $('#clichart9 a').attr('href');
		var urlcli9 = 'http://'+thisip+':9425/'+half;

		var half = $('#clichart10 a').attr('href');
		var urlcli10 = 'http://'+thisip+':9425/'+half;

		var half = $('#clichart11 a').attr('href');
		var urlcli11 = 'http://'+thisip+':9425/'+half;


		function doRendercli8(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

					/*var day = myDate.getDay();
					var month = myDate.getMonth();
					var year = myDate.getYear();

					var date = month+'/'+day+'/'+year;*/
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}

			   

			    	if ( ((min == '00') || (min == '30')) && hour.length < 3 ) {
			    	/*if (min != '00') {
			    		min = '00';
			    	}*/

			    	

			  		
			    	timeframe = hour+':'+min; 
			    	

			    	//firstval = Number((firstval).toFixed(2));
			    	if (firstval == '') {
			    		firstval = 0;
			    	}

			    	rendervar.push({
						period: timeframe,
						up: firstval
					});
		    	}
		    	
		    }
		    
		  

		    $('.preload8').hide();

		 Morris.Area({
			element: 'chart-client-8',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['bits'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData8(url, callBack) {
		    Papa.parse(url, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData8(urlcli8, doRendercli8);



		function doRendercli9(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

					/*var day = myDate.getDay();
					var month = myDate.getMonth();
					var year = myDate.getYear();

					var date = month+'/'+day+'/'+year;*/
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}

			    	if (min == '49') {
							hour = hour+1;
							min = '00';
						}

						if (min == '19') {
							min = '30';
						}
			   

			    	if ( ((min == '00') || (min == '30')) && hour.length < 3 ) {
			    	/*if (min != '00') {
			    		min = '00';
			    	}*/

			    	

			  		
			    	timeframe = date+'-'+hour+':'+min; 
			    	

			    	//firstval = Number((firstval).toFixed(2));
			    	if (firstval == '') {
			    		firstval = 0;
			    	}

			    	rendervar.push({
						period: timeframe,
						up: firstval
					});
		    	}
		    	
		    }
		    
		  

		    $('.preload9').hide();

		 Morris.Area({
			element: 'chart-client-9',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['bits'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData9(url, callBack) {
		    Papa.parse(url, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData9(urlcli9, doRendercli9);


		function doRendercli10(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

					/*var day = myDate.getDay();
					var month = myDate.getMonth();
					var year = myDate.getYear();

					var date = month+'/'+day+'/'+year;*/
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}

			   

			    	if ( ((min == '00') || (min == '30')) && hour.length < 3 ) {
			    	/*if (min != '00') {
			    		min = '00';
			    	}*/

			    	

			  		
			    	timeframe = hour+':'+min; 
			    	

			    	//firstval = Number((firstval).toFixed(2));
			    	if (firstval == '') {
			    		firstval = 0;
			    	}

			    	rendervar.push({
						period: timeframe,
						up: firstval
					});
		    	}
		    	
		    }
		    
		  

		    $('.preload10').hide();

		 Morris.Area({
			element: 'chart-client-10',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['bits'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData10(url, callBack) {
		    Papa.parse(url, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData10(urlcli10, doRendercli10);



		function doRendercli11(data) {
		    //Data is usable here
		    var rendervar = [];
		    

		    var lengther = data.length;
		    
		    for (i=1; i<lengther; i++) {
		    	

		    		var timeframe = data[i][0];
		    		timeframe = parseInt(timeframe);
		    		var timeframe = timeframe*1000-2460000;

			    	var dt=eval(timeframe);
					var myDate = new Date(dt);
					var date = myDate.toLocaleString();

					/*var day = myDate.getDay();
					var month = myDate.getMonth();
					var year = myDate.getYear();

					var date = month+'/'+day+'/'+year;*/
					var min = myDate.getUTCMinutes();
					var hour = myDate.getUTCHours();

										
						var ndate = date.split(',');
						date = ndate[0];

						if (date != 'Invalid Date') {
							$('.todate').text(date);
						}



					min = min.toString();
					hour = hour.toString();

					

			    	var firstval = data[i][1];
			    	var secondval = data[i][2];


			    	

			    	if (hour.length < 2) {
			    		hour = '0'+hour;
			    	}

			    	if (min.length < 2) {
			    		min = '0'+min;
			    	}

			   		if (min == '49') {
							hour = hour+1;
							min = '00';
						}

						if (min == '19') {
							min = '30';
						}

			    	if ( ((min == '00') || (min == '30')) && hour.length < 3 ) {
			    	/*if (min != '00') {
			    		min = '00';
			    	}*/

			    	

			  		
			    	timeframe = date+'-'+hour+':'+min; 
			    	

			    	//firstval = Number((firstval).toFixed(2));
			    	if (firstval == '') {
			    		firstval = 0;
			    	}

			    	rendervar.push({
						period: timeframe,
						up: firstval
					});
		    	}
		    	
		    }
		    
		  

		    $('.preload11').hide();

		 Morris.Area({
			element: 'chart-client-11',
			data: rendervar,
			gridEnabled: false,
			gridLineColor: 'transparent',
			behaveLikeLine: true,
			xkey: 'period',
			ykeys: ['up'],
			labels: ['bits'],
			lineColors: ['#045d97'],
			pointSize: 0,
			pointStrokeColors : ['#045d97'],
			lineWidth: 0,
			resize:true,
			hideHover: 'auto',
			fillOpacity: 0.7,
			parseTime:false
		});
		}

		function parseData11(url, callBack) {
		    Papa.parse(url, {
		        download: true,
		        dynamicTyping: true,
		        complete: function(results) {
		            callBack(results.data);
		        }
		    });
		}

		parseData11(urlcli11, doRendercli11);

}



function chartclienterase() {
	$('.clientside').hide();
	$('.clientchart').hide();
	$('#chart-client-1').html("");
	$('#chart-client-2').html("");
	$('#chart-client-3').html("");
	$('#chart-client-4').html("");
	$('#chart-client-5').html("");
	$('#chart-client-6').html("");
	$('#chart-client-7').html("");
	$('#chart-client-8').html("");
	$('#chart-client-9').html("");
	$('#chart-client-10').html("");
	$('#chart-client-11').html("");
	$('#chart-client-12').html("");

}