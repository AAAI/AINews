<?php

class mysql_db {

    var $db_connect_id;
    var $query_result;
    var $row = array();
    var $rowset = array();

    function mysql_db($dbhost, $dbuser, $dbpass, $database) {
        $this->server = $dbhost;
        $this->user = $dbuser;
        $this->password = $dbpass;
        $this->dbname = $database;
        $this->db_connect_id = @mysql_connect($this->server, $this->user, $this->password);
        if($this->db_connect_id) {
            if($database != "") {
                $this->dbname = $database;
                $dbselect = @mysql_select_db($this->dbname);
                if(!$dbselect) {
                    @mysql_close($this->db_connect_id);
                    $this->db_connect_id = $dbselect;
                }
            }
            return $this->db_connect_id;
        } else {
            return false;
        }
    }
    function sql_close() {
        if($this->db_connect_id) {
            if($this->query_result) {
                @mysql_free_result($this->query_result);
            }
            $result = @mysql_close($this->db_connect_id);
            return $result;
        } else {
            return false;
        }
    }
    function sql_fetchrow($query_id = 0) {
        if(!$query_id) {
            $query_id = $this->query_result;
        }
        if($query_id) {
            $this->row[$query_id] = @mysql_fetch_array($query_id);
            return $this->row[$query_id];
        } else {
            return false;
        }
    }
    function sql_fetchfield($query_id = 0, $field) {
        if(!$query_id) {
            $query_id = $this->query_result;
        }
        if($query_id) {
            $this->row[$query_id] = @mysql_fetch_field($query_id);
            return $this->row[$query_id];
        } else {
            return false;
        }
    }
    function sql_numfields($query_id = 0) {
        if(!$query_id) {
            $query_id = $this->query_result;
        }
        if($query_id) {
            $result = @mysql_num_fields($query_id);
            return $result;
        } else {
            return false;
        }
    }
    function sql_numrows($query_id = 0) {
        if(!$query_id) {
            $query_id = $this->query_result;
        }
        if($query_id) {
            $result = @mysql_num_rows($query_id);
            return $result;
        } else {
            return false;
        }
    }
    function sql_query($query = "") {
        unset($this->query_result);
        if($query != "") {
            $this->query_result = @mysql_query($query, $this->db_connect_id);
        }
        if($this->query_result) {
            unset($this->row[$this->query_result]);
            unset($this->rowset[$this->query_result]);
            return $this->query_result;
        } else {
            return false;
        }
    }
}

include_once("config.php");
$db = new mysql_db($dbhost, $dbuser, $dbpass, $database);

