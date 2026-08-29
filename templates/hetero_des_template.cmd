File {
  Grid    = "model_msh.tdr"
  Plot    = "model_iv.tdr"
  Current = "model_iv"
  Output  = "model_iv.log"
}
Electrode {
  { Name="anode"   Voltage=0.0 }
  { Name="cathode" Voltage=0.0 }
}

Physics {
  Fermi

  __THERMIONIC__

  Mobility(
    DopingDependence
  )

  Recombination(
    SRH
  )

  EffectiveIntrinsicDensity(
    __BGN_MODEL__
  )
}

Physics(Material="InGaAs") {
    MoleFraction(
        xFraction = __GA_FRACTION__
    )
}

Plot {
  eDensity
  hDensity
  eCurrent/Vector
  hCurrent/Vector
  TotalCurrent/Vector
  ElectricField/Vector
  Potential
  SpaceCharge
  Doping
  DonorConcentration
  AcceptorConcentration
  ConductionBand
  ValenceBand
  BandGap
  eQuasiFermi
  hQuasiFermi
}

Math {
  __GEOMETRY_OPTION__

  Method=ParDiSo
  Number_of_Threads=4
  WallClock
  Extrapolate
  RelErrControl
  Iterations=50
  NotDamped=100
  Digits=5
}

Solve {
  NewCurrentPrefix="init_"

  Coupled(Iterations=100) {
    Poisson
  }

  Coupled(Iterations=100) {
    Poisson
    Electron
    Hole
  }

  Save(FilePrefix="hetero_eqstate")
  Plot(FilePrefix="hetero_equilibrium")

  NewCurrentPrefix="pos_"

  Quasistationary(
    InitialStep=0.002
    Increment=1.25
    Decrement=2.0
    MinStep=1e-7
    MaxStep=0.02
    Goal {
      Name="anode"
      Voltage = __V_FORWARD__
    }
  ) {
    Coupled {
      Poisson
      Electron
      Hole
    }
    CurrentPlot(
      Time=(
        Range=(0 1)
        Intervals=100
      )
    )
  }

  Plot(FilePrefix="hetero_forward")

  Load(FilePrefix="hetero_eqstate")

  NewCurrentPrefix="neg_"

  Quasistationary(
    InitialStep=0.002
    Increment=1.25
    Decrement=2.0
    MinStep=1e-7
    MaxStep=0.02
    Goal {
      Name="anode"
      Voltage = __V_REVERSE__
    }
  ) {
    Coupled {
      Poisson
      Electron
      Hole
    }
    CurrentPlot(
      Time=(
        Range=(0 1)
        Intervals=100
      )
    )
  }

  Plot(FilePrefix="hetero_reverse")
}
