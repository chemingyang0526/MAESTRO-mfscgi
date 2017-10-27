<?php
/* header('Access-Control-Allow-Origin: *'); */
parse_str(implode('&', array_slice($argv, 1)), $_GET);

if (isset($_GET['label'])) {
	
	$filenamepath = '/etc/mfs/mfschunkserver.cfg';

	$file = file_get_contents($filenamepath);
	$matches = array();
	$pattern = '/^\s*#?\s*(LABEL =)+\s*.*?$/m';

	preg_match($pattern, $file, $matches);

	if (count($matches) > 0) {
		$newlabel = $_GET['label'];
		$replacement = '$1 '.$newlabel;
		$file = preg_replace($pattern, $replacement, $file);
		$write_success = file_put_contents($filenamepath, $file, LOCK_EX);
	} else {
		$write_success = file_put_contents($filenamepath, 'LABEL = '.$_GET['label'], FILE_APPEND | LOCK_EX);
	}

	if ($write_success) {
		$run_success = shell_exec('sudo /etc/init.d/lizardfs-chunkserver reload');
		$whoami = exec('whoami');


		//if ($run_success) {
		//	echo json_encode('server reloaded').PHP_EOL;
		//} else {
		//	echo json_encode('reload failed').PHP_EOL;
		//}
		echo json_encode($whoami).PHP_EOL;
	} else {
		echo json_encode('write failed').PHP_EOL;
	}
} else {
	echo json_encode("fetch label failed").PHP_EOL;
}
?>
