<?php

	// define where the TEITOK common files can be found
	$ttroot = getenv('TT_ROOT') ;
	if ( !$ttroot ) if ( is_dir("/home/git/TEITOK") ) $ttroot = "/home/git/TEITOK";
		else $ttroot = ".."; 

	// define which time-zone to use (obligatory for date in PHP)
	date_default_timezone_set('UTC');
	
	// define which errors to report
	ini_set('display_errors', '0');
	error_reporting(E_ERROR|E_WARNING);

	// call the main php script and only use resources from here
	include ( "$ttroot/common/Sources/main.php" );

?>
