---
title: 'lys_instr: A Python Package for Building Flexible GUIs to Automate Scientific Measurements (A Python Package for Automating Scientific Measurements)'
tags:
  - Python
  - instrument control
  - scientific measurements
authors:
  - name: Ziqian Wang
    orcid: 0000-0002-0282-5941
    corresponding: true
    affiliation: 1
  - name: Hidenori Tsuji
    affiliation: 2
  - name: Toshiya Shiratori
    orcid: 0009-0007-6199-1548
    affiliation: “2, 3”
  - name: Asuka Nakamura
    orcid: 0000-0002-3010-9475
    corresponding: true
    affiliation: 2
affiliations:
 - name: Research Institute for Quantum and Chemical Innovation, Institutes of Innovation for Future Society, Nagoya University, Japan
   index: 1
   ror: 04chrp450
 - name: RIKEN Center for Emergent Matter Science, Japan
   index: 2
   ror: 03gv2xk61
 - name: Department of Applied Physics, The University of Tokyo, Japan
   index: 3
   ror: 057zh3y96
date: 14 October 2025
bibliography: paper.bib
---

# Summary

Automating scientific measurements has become increasingly important for experimentalists and is now a standard practice in modern laboratories. Although many commercial instruments provide their control software, researchers often need to coordinate multiple devices within a unified workflow. While several workflow management frameworks exist, they are typically broad in scope and require substantial effort to adapt to specific experimental setups. We present *lys_instr*, a Python package designed for experimentalists to build customizable graphical user interfaces (GUIs) and automate device-based scientific workflows. The package features a streamlined, asynchronous architecture optimized for iterative device manipulation and data acquisition, enabling efficient definition and execution of nested measurement processes from the GUI. *lys_instr* also integrates seamlessly with the *lys* platform for data visualization and post-analysis. These features allow users to rapidly construct flexible control systems for complex experimental workflows with minimal time and coding effort.

# Statement of need

Modern experimental research increasingly relies on complex, multi-instrument setups that require efficient coordination of device control, data acquisition, and visualization. Existing frameworks such as QCoDeS [@QCoDeS], PyMeasure [@PyMeasure], PyLabControl [@PyLabControl], LabVIEW [@LabVIEW], and MATLAB’s Instrument Control Toolbox [@MATLAB] provide powerful ecosystems for hardware communication and measurement scripting. However, they often need extensive coding to construct or modify measurement workflows, posing a barrier for researchers focused on scientific discovery rather than software engineering.
*lys_instr* addresses this gap by providing a lightweight, streamlined framework for experiments based on the broadly applicable *move-and-detect* paradigm—common in physics, materials science, and related fields—where parameters are iteratively adjusted (“move”) and responses recorded (“detect”). Each such sequence is called a *scan*, and multiple scans can be nested into a *MultiScan* to form a complex, multidimensional workflow. Users can configure these nested workflows directly through the GUI, requiring minimal coding beyond basic hardware communication setup. This design lowers the barrier to automation and allows measurement logic to be reconfigured dynamically.
Unlike general-purpose suites, *lys_instr* decouples workflow orchestration from low-level communication protocols (e.g., VISA, serial, TCP/IP), giving users flexibility in integrating diverse instruments. Its architecture emphasizes efficient workflow structuring, asynchronous execution across devices, and a responsive GUI. Seamless integration with the *lys* platform provides a unified ecosystem linking acquisition, metadata management, visualization, and analysis. Together, these features make *lys_instr* a practical and accessible framework for laboratories seeking flexible and efficient experimental automation.

# Overview: Graphical Workflow Configuration

*lys_instr* is a GUI-driven framework designed for flexible and efficient experiment automation. Figure \autoref{fig:fig1} shows a typical GUI layout created with it, which is embedded within the *lys* application as a sub-window. The interface is organized into three primary interactive sectors:
- Sector A (Storage panel): Manages data file naming, metadata logging, and automatic asynchronous saving of acquired data. 
- Sector B (Detector panel): Displays live data from the instrument and provides controls for detector operation.
- Sector C (Motor and workflow control panel): Contains tabs for motor control and scan configuration. The **Scan** tab, shown in the Figure \autoref{fig:fig1}, forms the core of the *move-and-detect* paradigm.
Within the **Scan** tab, users can declaratively define multi-dimensional, nested scan sequences (*MultiScan*) by adding scan loops to the “Parameter list”. The hierarchy is clearly defined: inner processes appear above and outer ones below. These loops coordinate motor and detector operations. The base (lowest-level) process in a scan is typically a predefined detector process selected from the “Process” area. The **Motor** tab enables monitoring and control of all defined motor axes, whether they represent physical hardware or digital parameters. 
The seamless embedding of *lys_instr* within the *lys* platform allows advanced, on-the-fly customization of data visualization and detector displays on the right side of the main window. This GUI design allows users to configure and execute most device-based workflows for scientific research. Furthermore, advanced users can configure highly customized GUI layouts tailored to their specific purpose with minimal upper-level coding.

# Projects using the software

*lys_instr* has been actively deployed in high-complexity, real-world scientific instrumentation for projects leading to multiple publications. A primary example is its use in automating Ultrafast Transmission Electron Microscopy (UTEM) experiments at the RIKEN Center for Emergent Matter Science [@Nakamura:2023; @Nakamura:2020; @Nakamura:2021a; @Nakamura:2022; @Nakamura:2023a; @Nakamura:2018; @Shimojima:2023a; @Shimojima:2023b; @Shimojima:2021].

# Figures

![Representative GUI layout of *lys_instr*. The main window embedded in the *lys* window primarily consists of the Storage panel (A), Detector panel (B), and Motor and Scan tabs (C). The Scan tab allows dynamic configuration of the experimental workflow. This layout can be customized by users according to needs.\label{fig:fig1}](fig1.png)

# Acknowledgements

We acknowledge valuable comments from Takahiro Shimojima and Kyoko Ishizaka. This work was partially supported by a Grant-in-Aid for Scientific Research (KAKENHI) (Grant No. ).
