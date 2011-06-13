<?php
/*
  The AINewsEmail.php is used to send twice-monthly AINews notification for
  subscribers.
  It is called in the publish part in AINews.py.
*/

$paths = parse_ini_file("config/paths.ini", true);
$config = parse_ini_file("config/config.ini", true);

$AINEWS_DIR = $paths['ainews']['ainews_root'];
$PMWIKI_DIR = $paths['pmwiki']['dir'];
$OUTPUT_DIR = $paths['ainews']['output'];
$filename = $OUTPUT_DIR."email_output.txt";

$handle = fopen($filename, "r");
// message
$message = fread($handle, filesize($filename));
fclose($handle);

// multiple recipients
$subscribers = $config['email']['subscribers'];
$sub_array = explode(":", $subscribers);
$to = "";

foreach($sub_array as $sub){
	$to .= "$sub, ";	
}

// subject
$today = date("D, F j, Y");
$subject = "Weekly AI Alert, $today";

// To send HTML mail, the Content-type header must be set
$headers  = 'MIME-Version: 1.0' . "\r\n";
$headers .= 'Content-type: text/html; charset=utf-8' . "\r\n";

// Additional headers
$headers .= 'From: AI Alert<admin11@aaai.org>' . "\r\n";


// Mail it
print mail($to, $subject, $message, $headers);
?>
