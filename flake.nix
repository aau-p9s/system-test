{
    # make flake an exact copy of forecaster and extend it with `//`
    inputs.nixpkgs.url = "nixpkgs/nixos-24.05";
    inputs.forecaster.url = "github:aau-p9s/forecaster";
    inputs.forecaster.inputs.nixpkgs.follows = "nixpkgs";
    outputs = { forecaster, nixpkgs, ... }: forecaster // (let
        system = "x86_64-linux";
        pkgs = import nixpkgs { inherit system; };
    in {
        packages.${system}.test = pkgs.writeScriptBin "test" ''
            #!${pkgs.bash}/bin/bash
            ${forecaster.packages.${system}.env.interpreter} Test.py $@
        '';
    });
}
