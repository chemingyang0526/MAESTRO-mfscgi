<?php
parse_str(implode('&', array_slice($argv, 1)), $_GET);

if (isset($_GET['period']) && isset($_GET['action'])) {
	//$day = $_GET['day'];
	//$month = $_GET['month'];
	
	$period = $_GET['period'];
	$action = $_GET['action'];
	$day = date('d');
	$month = date('m');
	$year = date('Y');

	//$day = (string)$day;
	//$month = (string)$month;

	if (($month == '01') || ($month == '05') || ($month == '07') || ($month == '08') || ($month == '10') || ($month == '12')) {
		$brnum = 30;
	}

	if ($month == '03') {
		$brnum = 28;
	}


	if (($month == '02')|| ($month == '04') || ($month == '06') || ($month == '09') || ($month == '11')) {
		$brnum = 31;
	}

	

	if ($period == 'month') {
		$count = 0;
		$rez = 'timestamp,val1,val2,val3'.PHP_EOL;
		for ($i=$day; $i>0; $i--) {
			$count = $count++;
			$d = $i;
			$m = $month;

			if (strlen($d) < 2) {
				$d = '0'.$d;
			}

			if (strlen($m) < 2) {
				$m = '0'.$m;
			}
			$timestamp = $d.'.'.$m.'.'.$year;
			$filename = '/usr/share/mfscgi/csvdata/'.$action.'_m'.$m.'.d'.$d;
			
			if ($action == 'cpu') {
				if (file_exists($filename)) {
					$max = getcpumax($filename);
					$max = $max/450; 
					$max = round($max,2);
					$rez .= $timestamp.',0,'.$max.",0".PHP_EOL;
				} else {
					$rez .= $timestamp.",0,0,0".PHP_EOL;
				}
			}

			if ( ($action == 'memory') || ($action == 'deletion') || ($action == 'replication') || ($action == 'read') || ($action == 'write') || ($action == 'packets_received') || ($action == 'packets_write')) {
				if (file_exists($filename)) {
					$max = getmax($filename);
					//$max = round($max,2);
					$rez .= $timestamp.','.$max.PHP_EOL;
				} else {
					$rez .= $timestamp.",0".PHP_EOL;
				}
			}


			
		}
		
		if ($count < $brnum) {
			$ncount = $brnum - $count;
		
			for ($i=$ncount; $i>0; $i--) {
			
			$d = $i;
			$m = $month-1;
			if ($d == $day) {
				break;
			}


			if (strlen($d) < 2) {
				$d = '0'.$d;
			}

			if (strlen($m) < 2) {
				$m = '0'.$m;
			}
			$timestamp = $d.'.'.$m.'.'.$year;
			$filename = '/usr/share/mfscgi/csvdata/'.$action.'_m'.$m.'.d'.$d;

		
			 
			if ($action == 'cpu') {
			 	if (file_exists($filename)) {
					$max = getcpumax($filename);
					$max = $max/450; 
					$max = round($max,2);
					$rez .= $timestamp.',0,'.$max.",0".PHP_EOL;
				} else {
					
					$rez .= $timestamp.",0,0,0".PHP_EOL;
				}
			}

			if ( ($action == 'memory') || ($action == 'deletion') || ($action == 'replication') || ($action == 'read') || ($action == 'write') || ($action == 'packets_received') || ($action == 'packets_write')) {
			 	if (file_exists($filename)) {
					$max = getmax($filename); 
					//$max = round($max,2);
					$rez .= $timestamp.','.$max.PHP_EOL;
				} else {
					
					$rez .= $timestamp.",0".PHP_EOL;
				}
			}
			
			
		}
		}

		echo $rez;
	}

	if ($period == 'week') {
		$count = 0;
		$rez = 'timestamp,val1,val2,val3'.PHP_EOL;
		
		for ($i=$day; $i>0; $i--) {

			if ($count == 7) {
				break;
			}

			$count = $count+1;
			$d = $i;
			$m = $month;

			if (strlen($d) < 2) {
				$d = '0'.$d;
			}

			if (strlen($m) < 2) {
				$m = '0'.$m;
			}
			$timestamp = $d.'.'.$m.'.'.$year;
			$filename = '/usr/share/mfscgi/csvdata/'.$action.'_m'.$m.'.d'.$d;
			
			

			if ($action == 'cpu') {
				if (file_exists($filename)) {
					$max = getcpumaxweek($filename);
					
						$max[0] = $max[0]/450;
						$max[0] = round($max[0],2);
						$rez .= $timestamp.',0,'.$max[0].",0".PHP_EOL;
						
						$max[1] = $max[1]/450;
						$max[1] = round($max[1],2);
						$rez .= $timestamp.',0,'.$max[1].",0".PHP_EOL;
						
						$max[2] = $max[2]/450;
						$max[2] = round($max[2],2);
						$rez .= $timestamp.',0,'.$max[2].",0".PHP_EOL;

						$max[3] = $max[3]/450;
						$max[3] = round($max[3],2);
						$rez .= $timestamp.',0,'.$max[3].",0".PHP_EOL;

				} else {
					$rez .= $timestamp.",0,0,0".PHP_EOL;
				}
			}

			if ( ($action == 'memory') || ($action == 'deletion') || ($action == 'replication') || ($action == 'read') || ($action == 'write') || ($action == 'packets_received') || ($action == 'packets_write') ) {
				if (file_exists($filename)) {
					$max = getmaxweek($filename);
					
						
						$max[0] = round($max[0],2);
						$rez .= $timestamp.','.$max[0].PHP_EOL;
						
						
						$max[1] = round($max[1],2);
						$rez .= $timestamp.','.$max[1].PHP_EOL;
						
						
						$max[2] = round($max[2],2);
						$rez .= $timestamp.','.$max[2].PHP_EOL;

					
						$max[3] = round($max[3],2);
						$rez .= $timestamp.','.$max[3].PHP_EOL;

				} else {
					$rez .= $timestamp.",0".PHP_EOL;
				}
			}
		}

		
		if ($count < 7) {
			$ncount = $brnum - $count;
			
			for ($i=$ncount; $i>0; $i--) {
				$count = $count + 1;
				
				if ($count == 8) {
					break;
				}
				$d = $i;
				$m = $month-1;
				
				if (strlen($d) < 2) {
					$d = '0'.$d;
				}

				if (strlen($m) < 2) {
					$m = '0'.$m;
				}

				$timestamp = $d.'.'.$m.'.'.$year;
				$filename = '/usr/share/mfscgi/csvdata/'.$action.'_m'.$m.'.d'.$d;
				
				

				if ($action == 'cpu') {
					if (file_exists($filename)) {
					 	
						$max = getcpumaxweek($filename);

						$max[0] = $max[0]/450;
						$max[0] = round($max[0],2);
						$rez .= $timestamp.',0,'.$max[0].",0".PHP_EOL;
						
						$max[1] = $max[1]/450;
						$max[1] = round($max[1],2);
						$rez .= $timestamp.',0,'.$max[1].",0".PHP_EOL;
						
						$max[2] = $max[2]/450;
						$max[2] = round($max[2],2);
						$rez .= $timestamp.',0,'.$max[2].",0".PHP_EOL;

						$max[3] = $max[3]/450;
						$max[3] = round($max[3],2);
						$rez .= $timestamp.',0,'.$max[3].",0".PHP_EOL;

					} else {
						
						$rez .= $timestamp.",0,0,0".PHP_EOL;
					}
				}

				if ( ($action == 'memory') || ($action == 'deletion') || ($action == 'replication') || ($action == 'read') || ($action == 'write') || ($action == 'packets_received') || ($action == 'packets_write') ) {
				if (file_exists($filename)) {
					$max = getmaxweek($filename);
					
						
						$max[0] = round($max[0],2);
						$rez .= $timestamp.','.$max[0].PHP_EOL;
						
						
						$max[1] = round($max[1],2);
						$rez .= $timestamp.','.$max[1].PHP_EOL;
						
						
						$max[2] = round($max[2],2);
						$rez .= $timestamp.','.$max[2].PHP_EOL;

					
						$max[3] = round($max[3],2);
						$rez .= $timestamp.','.$max[3].PHP_EOL;

				} else {
					$rez .= $timestamp.",0".PHP_EOL;
				}
			}


			}
		}

		echo $rez;
	}


} else {
	die();
}


function getcpumax($filename) {
	$file = fopen($filename,"r");
	
	$max = 0;
	while(! feof($file)) {
		$csv = fgetcsv($file);
		if ($csv[2] > $max) {
			$max = $csv[2];
		}
	}				
	fclose($file);
	return $max;
}

function getmax($filename) {
	$file = fopen($filename,"r");
	
	$max = 0;
	while(! feof($file)) {
		$csv = fgetcsv($file);

		if ($csv[1] > $max) {
			$max = $csv[1];
		}
	}				
	fclose($file);
	//var_dump($max);
	return $max;
}


function getcpumaxweek($filename) {
	$file = fopen($filename,"r");
	
	$max = array();
	$max[0] = 0;
	$max[1] = 0;
	$max[2] = 0;
	$max[3] = 0;

	
	
	$brnum = 237;
	$brnum2 = 237*2;
	$brnum3 = 237*3;
	$brnum4 = 237*4;
	

	
	$count = 0;
	while(!feof($file)) {
		$csv = fgetcsv($file);

		if ($count < $brnum) {
			if ($csv[2] > $max[0]) {
				$max[0] = $csv[2];
			}
		}

		if ( ($count > $brnum) && ($count < $brnum2) ) {
			if ($csv[2] > $max[1]) {
				$max[1] = $csv[2];
			}
		}

		if ( ($count > $brnum2) && ($count < $brnum3) ) {
			if ($csv[2] > $max[2]) {
				$max[2] = $csv[2];
			}
		}

		if ( ($count > $brnum3) && ($count < $brnum4) ) {
			if ($csv[2] > $max[3]) {
				$max[3] = $csv[2];
			}
		}
		$count = $count+1;
	}				
	fclose($file);
	return $max;
}

function getmaxweek($filename) {
	$file = fopen($filename,"r");
	
	$max = array();
	$max[0] = 0;
	$max[1] = 0;
	$max[2] = 0;
	$max[3] = 0;

	
	
	$brnum = 237;
	$brnum2 = 237*2;
	$brnum3 = 237*3;
	$brnum4 = 237*4;
	

	
	$count = 0;
	while(!feof($file)) {
		$csv = fgetcsv($file);

		if ($count < $brnum) {
			if ($csv[1] > $max[0]) {
				$max[0] = $csv[1];
			}
		}

		if ( ($count > $brnum) && ($count < $brnum2) ) {
			if ($csv[1] > $max[1]) {
				$max[1] = $csv[1];
			}
		}

		if ( ($count > $brnum2) && ($count < $brnum3) ) {
			if ($csv[1] > $max[2]) {
				$max[2] = $csv[1];
			}
		}

		if ( ($count > $brnum3) && ($count < $brnum4) ) {
			if ($csv[1] > $max[3]) {
				$max[3] = $csv[1];
			}
		}
		$count = $count+1;
	}				
	fclose($file);

	return $max;
}


?>