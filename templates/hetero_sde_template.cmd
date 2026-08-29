; =========================================================
; Automatic SDE template
; =========================================================

(sde:clear)
(sdegeo:set-default-boolean "ABA")


; -------------------------
; Geometry
; -------------------------

(define W            __WIDTH_UM__)

(define tNTop        __T_NTOP_UM__)
(define tNInGaAs     __T_NINGAAS_UM__)
(define tIInGaAs     __T_IINGAAS_UM__)
(define tP           __T_P_UM__)
(define tIGaAs       __T_IGAAS_UM__)
(define tNBottom     __T_NBOTTOM_UM__)


; -------------------------
; Doping
; -------------------------

(define NdTop        __ND_TOP__)
(define NdNInGaAs    __ND_NINGAAS__)
(define NdIInGaAs    __ND_IINGAAS__)
(define NaPBarrier   __NA_P__)
(define NdIGaAs      __ND_IGAAS__)
(define NdBottom     __ND_BOTTOM__)


; -------------------------
; Layer coordinates
; -------------------------

(define y0 0.000)
(define y1 (+ y0 tNTop))
(define y2 (+ y1 tNInGaAs))
(define y3 (+ y2 tIInGaAs))
(define y4 (+ y3 tP))
(define y5 (+ y4 tIGaAs))
(define y6 (+ y5 tNBottom))

(sdegeo:create-rectangle (position 0.0 y0 0.0) (position W y1 0.0) "GaAs"   "R.nTop")
(sdegeo:create-rectangle (position 0.0 y1 0.0) (position W y2 0.0) "InGaAs" "R.nInGaAs")
(sdegeo:create-rectangle (position 0.0 y2 0.0) (position W y3 0.0) "InGaAs" "R.iInGaAs")
(sdegeo:create-rectangle (position 0.0 y3 0.0) (position W y4 0.0) "GaAs"   "R.pBarrier")
(sdegeo:create-rectangle (position 0.0 y4 0.0) (position W y5 0.0) "GaAs"   "R.iGaAs")
(sdegeo:create-rectangle (position 0.0 y5 0.0) (position W y6 0.0) "GaAs"   "R.nBottom")

(sdegeo:define-contact-set "anode" 4 (color:rgb 1.0 0.0 0.0) "##")
(sdegeo:set-current-contact-set "anode")
(sdegeo:define-2d-contact (find-edge-id (position (/ W 2.0) y0 0.0)) "anode")

(sdegeo:define-contact-set "cathode" 4 (color:rgb 0.0 0.0 1.0) "##")
(sdegeo:set-current-contact-set "cathode")
(sdegeo:define-2d-contact (find-edge-id (position (/ W 2.0) y6 0.0)) "cathode")

; -------------------------
; Doping profiles
; -------------------------

(sdedr:define-constant-profile
  "Dop.nTop"
  "NDopantActiveConcentration"
  NdTop
)
(sdedr:define-constant-profile-region
  "Place.nTop"
  "Dop.nTop"
  "R.nTop"
)


(sdedr:define-constant-profile
  "Dop.nInGaAs"
  "NDopantActiveConcentration"
  NdNInGaAs
)
(sdedr:define-constant-profile-region
  "Place.nInGaAs"
  "Dop.nInGaAs"
  "R.nInGaAs"
)


(sdedr:define-constant-profile
  "Dop.iInGaAs"
  "NDopantActiveConcentration"
  NdIInGaAs
)
(sdedr:define-constant-profile-region
  "Place.iInGaAs"
  "Dop.iInGaAs"
  "R.iInGaAs"
)


(sdedr:define-constant-profile
  "Dop.pBarrier"
  "PDopantActiveConcentration"
  NaPBarrier
)
(sdedr:define-constant-profile-region
  "Place.pBarrier"
  "Dop.pBarrier"
  "R.pBarrier"
)


(sdedr:define-constant-profile
  "Dop.iGaAs"
  "NDopantActiveConcentration"
  NdIGaAs
)
(sdedr:define-constant-profile-region
  "Place.iGaAs"
  "Dop.iGaAs"
  "R.iGaAs"
)


(sdedr:define-constant-profile
  "Dop.nBottom"
  "NDopantActiveConcentration"
  NdBottom
)
(sdedr:define-constant-profile-region
  "Place.nBottom"
  "Dop.nBottom"
  "R.nBottom"
)

(sdedr:define-refeval-window
  "Win.global"
  "Rectangle"
  (position 0.0 y0 0.0)
  (position W y6 0.0)
)

(sdedr:define-refinement-size
  "Ref.global"
  0.250 0.010
  0.050 0.001
)

(sdedr:define-refinement-placement
  "PlaceRef.global"
  "Ref.global"
  "Win.global"
)

(sdedr:define-refeval-window "Win.barrierArea" "Rectangle"
  (position 0.0 (- y1 0.005) 0.0)
  (position W   (+ y4 0.010) 0.0)
)
(sdedr:define-refinement-size
  "Ref.barrierArea"
  0.250
  __MESH_BARRIER_MAXY__
  0.050
  __MESH_BARRIER_MINY__
)
(sdedr:define-refinement-placement "PlaceRef.barrierArea" "Ref.barrierArea" "Win.barrierArea")

(sdedr:define-refeval-window "Win.pBarrier" "Rectangle" (position 0.0 y3 0.0) (position W y4 0.0))
(sdedr:define-refinement-size
  "Ref.pBarrier"
  0.250
  __MESH_P_MAXY__
  0.050
  __MESH_P_MINY__
)
(sdedr:define-refinement-placement "PlaceRef.pBarrier" "Ref.pBarrier" "Win.pBarrier")

; =========================================================
; i-GaAs refinement for breakdown analysis
; =========================================================

(sdedr:define-refeval-window
  "Win.iGaAs"
  "Rectangle"
  (position 0.0 y4 0.0)
  (position W   y5 0.0)
)

(sdedr:define-refinement-size
  "Ref.iGaAs"
  0.250
  __MESH_IGAAS_MAXY__
  0.050
  __MESH_IGAAS_MINY__
)

(sdedr:define-refinement-placement
  "PlaceRef.iGaAs"
  "Ref.iGaAs"
  "Win.iGaAs"
)

(sde:save-model "model")
(sde:build-mesh "snmesh" "-a -c boxmethod" "model_msh")
