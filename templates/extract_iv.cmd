proc write_curve {curve_name file_name} {

    set xs [cv_getValsX $curve_name]
    set ys [cv_getValsY $curve_name]

    set f [open $file_name "w"]

    puts $f "voltage current"

    foreach x $xs y $ys {
        puts $f "$x $y"
    }

    close $f
}


# FORWARD

proj_load "pos_model_iv_des.plt" FWD

cv_create IV_FWD \
    "FWD anode OuterVoltage" \
    "FWD anode TotalCurrent"

write_curve IV_FWD "model_forward.txt"


# REVERSE

proj_load "neg_model_iv_des.plt" REV

cv_create IV_REV \
    "REV anode OuterVoltage" \
    "REV anode TotalCurrent"

write_curve IV_REV "model_reverse.txt"


script_exit