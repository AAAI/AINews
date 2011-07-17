<?php
include_once("../config.php");
include_once("../functions.php");

$str = $_POST['words'];
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

$words = explode("\n",$str);

$res = "";
$postWords = array();

/* Checking words before calculate similarity*/
foreach($words as $word){
	$pword = $client->stem( trim($word) );
	if(!is_null($pword) && $pword != "") {
		if( $client->checkSense($pword) == 0){
			$res.=	"Word <strong>".$pword."</strong> is not noun.<br/>";
		}
		else {$postWords[] = $pword;}
	}else{
		$res .= "Word <strong>".$word."</strong> can't be recognized.<br/>";
	}
}

/* Calculate mutual similarity for any two words in the array*/
$size = count($postWords);
$res ="Total $size Words:<br/>";
$counts=1;

for($i = 0; $i < $size; ++$i) for($j = $i+1; $j < $size; ++$j){
	$res.="(".$counts++.") ";
	$res .= "<strong>".$postWords[$i].' ~ '.$postWords[$j]."</strong>: ".$client->query($postWords[$i],$postWords[$j], $strategy, $alpha)."<br/>";
}

echo $res;

if(strcmp($email, "")){
	sendEmail($email, "ldong@clemson.edu", $res);	
}