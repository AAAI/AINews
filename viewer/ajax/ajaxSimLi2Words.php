<?php
include_once("../config.php");

$word1 = $_POST['word1'];
$word2 = $_POST['word2'];
$alpha = $_POST['alpha'];
$beta  = $_POST['beta'];
$strategy = "li";

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
	echo "Word1 <strong>".$_POST['word1']."</strong> can't be recognized.\n";
}
else if(is_null($word2)){
	echo "Word2 <strong>".$_POST['word2']."</strong> can't be recognized.\n";
}
else{
	if($client->checkSense($word1) == 0){
		echo "Word1 <strong>".$word1."</strong> is not noun.\n";
	}
	else if($client->checkSense($word2) == 0){
		echo "Word2 <strong>".$word2."</strong> is not noun.\n";
	}
	else {
		//Need to pass five parameters for calling Li's method. Strategy number is 11 or name "li" for Li's method.
		echo "<strong>".$word1.' ~ '.$word2."</strong>: ".$client->query($word1,$word2, $strategy, $alpha, $beta)."\n";
	}
	
}

