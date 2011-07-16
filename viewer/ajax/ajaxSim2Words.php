<?php
include_once("../config.php");
include_once("../functions.php");

$word1 = $_POST['word1'];
$word2 = $_POST['word2'];
$alpha = $_POST['alpha'];
$strategy = $_POST['strategy'];
$email = $_POST['email'];

$client = new SoapClient(NULL,
            array(
            "location" => "http://".$ws_host.":".$ws_port."/",
            "uri"      => $ws_uri,
            "style"    => SOAP_RPC,
            "use"      => SOAP_ENCODED
          ));

          
$word1 = $client->stem($word1);
$word2 = $client->stem($word2);

if(is_null($word1)){
	$res = "Word1 <strong>".$_POST['word1']."</strong> can't be recognized.\n";
}
else if(is_null($word2)){
	$res = "Word2 <strong>".$_POST['word2']."</strong> can't be recognized.\n";
}
else{
	if($client->checkSense($word1) == 0){
		$res = "Word1 <strong>".$word1."</strong> is not noun.\n";
	}
	else if($client->checkSense($word2) == 0){
		$res = "Word2 <strong>".$word2."</strong> is not noun.\n";
	}
	else{
		$res = "<strong>".$word1.' ~ '.$word2."</strong>: ".$client->query($word1,$word2, $strategy, $alpha)."\n";
	}
}

echo $res;

if(strcmp($email, "")){
	sendEmail($email, "ldong@clemson.edu", $res);	
}