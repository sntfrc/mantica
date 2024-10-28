<?php
    /*
      Mantica - Copyright © 2024 Federico Santandrea.
      All rights reserved.
      
      Unauthorized copying, distribution, or use of this software in whole or in part
      is prohibited without the express written permission of the copyright holder.
    */

    // error_reporting(E_ALL);
    // ini_set('display_errors', 1);

    define("LOG_ENABLED", true);
    define("DISABLE_LOG_COMMAND", "!");

    define("PROMPT_ADDENDUM", "");
    define("NEGATIVE_PROMPT", "nsfw, naked");
    define("BAN_TERMS", array("nude", "naked", "blood", "dead"));

    function post_replicate($input, $model=NULL) {
        if ($model == NULL) {
            $model = "";
        } else {
            $model = "models/" . $model . "/";
        }

        $json_payload = json_encode($input);
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, "https://api.replicate.com/v1/" . $model . "predictions");
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $json_payload);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            "Authorization: Bearer " . trim(file_get_contents("r8_token")),
            'Content-Type: application/json',
            'Content-Length: ' . strlen($json_payload)
        ]);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        $response = curl_exec($ch);

        if ($response === false) {
            $ret = ["error" => curl_error($ch)];
            curl_close($ch);
            return $ret;
        }

        curl_close($ch);
        return json_decode($response);
    }

    function get_replicate($url) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            "Authorization: Bearer " . trim(file_get_contents("r8_token"))
        ]);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

        while (true) {
            set_time_limit(30);
            sleep(1);

            $response = curl_exec($ch);

            if (!$response) {
                $ret = ["error" => curl_error($ch)];
                curl_close($ch);
                return $ret;
            }

            $ret = json_decode($response);

            if ($ret->error != null) {
                return ["error" => $ret->error];
            }
            
            if ($ret->output != null) {
                return $ret->output;
            }
        }
    }

    if (isset($_GET["dream"])) {
        $ps = floatval($_GET["dream"]) / 100.0;
        $image_data = file_get_contents("php://input");

        $custom = empty($_GET["custom"]) ? "" : $_GET["custom"];

        if (LOG_ENABLED && !str_contains($custom, DISABLE_LOG_COMMAND)) {
            $decoded = base64_decode(explode(",", $image_data, 2)[1]);
            $filename = date("YmdHis") . "-" . $_SERVER["REMOTE_ADDR"];
            $filename = str_replace(".", "-", $filename);
            $filename = str_replace(":", "-", $filename);
            file_put_contents("logs/" . $filename . ".jpg", $decoded);
        }

        $custom = trim(str_replace(DISABLE_LOG_COMMAND, "", $custom));

        $ret = post_replicate([
            "version" => "2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
            "input" => [
                "image" => $image_data,
                "task" => "image_captioning"
            ]
        ]);

        $desc = str_replace("Caption: ", "", get_replicate($ret->urls->get));
        $prompt = str_replace(BAN_TERMS, "", trim($desc));
        $prompt = str_replace("  ", " ", $prompt);
        $prompt = str_replace(array(",,", " ,"), ", ", $prompt);

        if ($custom != NULL && $custom != "") {
            $prompt = $prompt . ", " . $custom;
        } else {
            $prompt = $prompt . ", " . PROMPT_ADDENDUM;
        }

        $ret = post_replicate([
            "input" => [
                "prompt" => $prompt,
                "aspect_ratio" => "1:1",
                "image" => $image_data,
                "prompt_strength" => $ps,
                "num_outputs" => 1,
                "num_inference_steps" => 28,
                "guidance" => 3.5,
                "output_format" => "png",
                "output_quality" => 100,
                "negative_prompt" => NEGATIVE_PROMPT,
                "go_fast" => true
            ]
        ], "black-forest-labs/flux-dev");

        $img_url = get_replicate($ret->urls->get)[0];
        echo(json_encode([
            "image" => $img_url,
            "caption" => $desc
        ]));
        die();
    }
?>
