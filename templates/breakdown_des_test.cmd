File {
  Grid    = "model_msh.tdr"
  Plot    = "breakdown.tdr"
  Current = "breakdown_iv"
  Output  = "breakdown.log"
}


Electrode {
  { Name="anode"   Voltage=0.0 }
  { Name="cathode" Voltage=0.0 }
}


Physics {

  Fermi

  Mobility(
    DopingDependence
  )

  Recombination(
    SRH
    Avalanche(ElectricField)
  )

  EffectiveIntrinsicDensity(
    OldSlotboom
  )
}


Physics(Material="InGaAs") {

  MoleFraction(
    xFraction=0.75
  )
}


Plot {

  eDensity
  hDensity

  ElectricField/Vector
  Potential
  SpaceCharge

  Doping
  DonorConcentration
  AcceptorConcentration

  ConductionBand
  ValenceBand
  BandGap

  eIonIntegral
  hIonIntegral
  MeanIonIntegral

  eAlphaAvalanche
  hAlphaAvalanche
}


Math {

  Cylindrical

  Method=ParDiSo
  Number_of_Threads=4
  WallClock

  Extrapolate
  RelErrControl

  Iterations=50
  NotDamped=100
  Digits=5

  ComputeIonizationIntegrals

  BreakAtIonIntegral(
    1
    1.05
  )
}


Solve {

  NewCurrentPrefix="init_"


  Coupled(
    Iterations=100
  ) {
    Poisson
  }


  Coupled(
    Iterations=100
  ) {
    Poisson
    Electron
    Hole
  }


  Save(
    FilePrefix="breakdown_eqstate"
  )


  Plot(
    FilePrefix="breakdown_equilibrium"
  )


  NewCurrentPrefix="bd_"


    Quasistationary(

    InitialStep=0.0002

    Increment=1.20
    Decrement=2.0

    MinStep=1e-7
    MaxStep=0.001

    Goal {
        Name="anode"
        Voltage=-20.0
    }

    ) {

    Coupled {
      Poisson
    }


    CurrentPlot(
    Time=(
        Range=(0 1)
        Intervals=800
    )
    )

  }


  Plot(
    FilePrefix="breakdown_final"
  )
}