{
    # make flake an exact copy of forecaster
    inputs.forecaster.url = "github:aau-p9s/forecaster/fix/wait-for-finish";
    outputs = { forecaster, ... }: forecaster;
}
