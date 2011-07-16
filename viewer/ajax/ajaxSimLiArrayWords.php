<?php
include_once("../config.php");

$str = $_POST['wordPairs'];
$alpha = $_POST['alpha'];
$beta = $_POST['beta'];
$strategy = "li";

$client = new SoapClient(NULL,
            array(
            "location" => "http://".$ws_host.":".$ws_port."/",
            "uri"      => $ws_uri,
            "style"    => SOAP_RPC,
            "use"      => SOAP_ENCODED
          ));

$wordPairs = explode("\n",$str);
$size = count($wordPairs);
$res ="Total $size Pairs:<br/>";

for($i=0; $i<$size; ++$i){
    $trimmed = trim($wordPairs[$i]);
	$pair = preg_split("/[\s]+/", $trimmed);
	$word1 = $client->stem($pair[0]);
	$word2 = $client->stem($pair[1]);
	$res.="(".($i+1).") ";
	if(is_null($word1)){
		$res .= "Word1 <strong>".$pair[0]."</strong> can't be recognized.<br/>";
	}
	else if(is_null($word2)){
		$res .= "Word2 <strong>".$pair[1]."</strong> can't be recognized.<br/>";
	}
	else{
		if($client->checkSense($word1) == 0){
			$res .= "Word1 <strong>".$word1."</strong> is not noun.<br/>";
		}
		else if($client->checkSense($word2) == 0){
			$res .= "Word2 <strong>".$word2."</strong> is not noun.<br/>";
		}
		else{
			$res .= "<strong>".$word1.' ~ '.$word2."</strong>: ".$client->query($word1,$word2, $strategy, $alpha, $beta)."<br/>";
		}
	}	
	
}

echo $res;

