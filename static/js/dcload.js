COLORS = ["red", "green", "blue", "white", "magenta", "yellow", "cyan",  "black", "orange"];

function dcload() {
    onPowerOn = function() {
        var button_selector = "#power-on";
        var icon_selector = "#icon-power-on";
        console.log("PowerOn");
        $(".btn-power").removeClass("active");
        $(".icon-power").hide();
        $(button_selector).addClass("active");
        $(icon_selector).show();
/*        if (dcload.postUI) {
            dcload.setPower(true);
        }*/
    }

    onPowerOff = function() {
        var button_selector = "#power-off";
        var icon_selector = "#icon-power-off";
        console.log("PowerOff");
        $(".btn-power").removeClass("active");
        $(".icon-power").hide();
        $(button_selector).addClass("active");
        $(icon_selector).show();
/*        if (dcload.postUI) {
            dcload.setPower(false);
        }*/
    }

    onMaChange = function() {
        ma = $("#slider-ma").slider("value");
        a = parseFloat(ma)/1000
        $("#ma-setPoint").text(a.toFixed(3) + " A");
        if (dcload.postUI) {
            dcload.sendDesiredMa(ma);
            dcload.ignoreOne = true;
        }
    }

    onMaSlide = function(event, ui) {
        ma = ui.value;
        a = parseFloat(ma)/1000
        $("#ma-setPoint").text(a.toFixed(3) + " A");
    }

    onMaStartSlide = function() {
        console.log("startSlide");
        dcload.maSliding=true;
    }

    onMaStopSlide = function() {
        console.log("stopSlide");
        dcload.maSliding=false;
    }

    sendDesiredMa = function(value) {
        $.ajax({url: "/dcload/setDesiredMa?value=" + value});
    }

    maPlus = function(value) {
        ma = parseFloat($("#slider-ma").slider("value"));
        ma = Math.min(10000, ma+value)    
        $("#slider-ma").slider({value: ma}); 
        dcload.ignoreOne = true;
    }

    maMinus = function(value) {
        ma = parseFloat($("#slider-ma").slider("value"));
        ma = Math.max(0, ma-value)    
        $("#slider-ma").slider({value: ma}); 
        dcload.ignoreOne = true;
    }

    maSet = function(value) {
        ma = parseFloat($("#ma-set-edit").val())*1000;
        $("#slider-ma").slider({value: ma}); 
        dcload.ignoreOne = true;
    }


    initButtons = function() {
        $("#slider-ma").slider({min: 1,
            max:10000,
            slide: this.onMaSlide,
            change: this.onMaChange,
            start: this.onMaStartSlide,
            stop: this.onMaStopSlide});

        $("#ma-plus-1").click(function() { dcload.maPlus(1); });
        $("#ma-plus-10").click(function() { dcload.maPlus(10); });
        $("#ma-plus-100").click(function() { dcload.maPlus(100); });
        $("#ma-plus-1000").click(function() { dcload.maPlus(1000); });

        $("#ma-minus-1").click(function() { dcload.maMinus(1); });
        $("#ma-minus-10").click(function() { dcload.maMinus(10); });
        $("#ma-minus-100").click(function() { dcload.maMinus(100); });
        $("#ma-minus-1000").click(function() { dcload.maMinus(1000); });

        $("#ma-set").click(function() { dcload.maSet(); });

        $("#power-on").click(function() { dcload.onPowerOn(); });
        $("#power-off").click(function() { dcload.onPowerOff(); });

    }

    parseStatus = function(settings) {
        //console.log(settings);
        this.postUI = false;
        try {
            if (dcload.ignoreOne) {
                dcload.ignoreOne = false;
            } else {
                if (!dcload.maSliding) {
                    $("#slider-ma").slider({value: settings.desired_ma});
                }
            }
            if (settings["actual_ma"]) {
                a = settings["actual_ma"]/1000.0;
                $("#actual-ma").text(a.toFixed(3) + " A");
            }
            if (settings["actual_volts"]) {
                $("#actual-volts").text(settings["actual_volts"].toFixed(3) + " V");
            }
            if (settings["actual_watts"]) {
                $("#actual-watts").text(settings["actual_watts"].toFixed(2) + " W");
            }
            if (settings["actual_temp"]) {
                $("#actual-temp").text(settings["actual_temp"].toFixed(1) + " C");
            }
            if (settings["power"]) {
                if (! $("#power-on").hasClass("active") ) {
                    $("#icon-power-on").click();
                }
            } else {
                if (! $("#power-off").hasClass("active") ) {
                    $("#icon-power-off").click();
                }
            }
        }
        finally {
            this.postUI = true;
        }
    }

    requestStatus = function() {
        $.ajax({
            url: "/dcload/getStatus",
            dataType : 'json',
            type : 'GET',
            success: function(newData) {
                dcload.parseStatus(newData);
                setTimeout("dcload.requestStatus();", 1000);
            },
            error: function() {
                console.log("error retrieving settings");
                setTimeout("dcload.requestStatus();", 5000);
            }
        });
    }

    start = function() {
         this.postUI = true;
         this.initButtons();
         this.requestStatus();
    }

    return this;
}

$(document).ready(function(){
    dcload = dcload()
    dcload.start();
});

