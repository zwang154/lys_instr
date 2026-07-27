---
title: 'lys_instr: A Python Package for Automating Scientific Measurements'
tags:
  - Python
  - instrument control
  - scientific measurements
authors:
  - name: Ziqian Wang
    orcid: 0000-0002-0282-5941
    corresponding: true
    affiliation: 1, 2
  - name: Hidenori Tsuji
    affiliation: 2
  - name: Toshiya Shiratori
    orcid: 0009-0007-6199-1548
    affiliation: 3
  - name: Asuka Nakamura
    orcid: 0000-0002-3010-9475
    affiliation: 2, 3
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
date: 14 November 2025
bibliography: paper.bib
---

# Summary

Modern experiments increasingly demand automation frameworks that coordinate diverse scientific instruments while remaining flexible and customizable. Developing custom measurement systems, however, often requires explicit management of low-level device communication and concurrency, resulting in substantial development overhead. We present `lys_instr`, a Python package that addresses these challenges through an object-oriented, three-layer architecture for scan-based instrument control, workflow coordination, and GUI construction. It enables researchers to construct responsive, asynchronous measurement systems by reusing instrument abstractions, workflow logic, and GUI components across hardware configurations. Integrated with the `lys` platform [@Nakamura:2023], `lys_instr` provides a common environment for experiment control, data acquisition, and multidimensional visualization.

# Statement of need

Modern scientific research increasingly relies on comprehensive measurements across wide parameter spaces to elucidate physical phenomena. As experiments grow in complexity—with longer measurement times and greater instrument diversity—efficient automation has become essential. Measurement automation is extending beyond fixed parameter scans toward informatics-driven, condition-based optimization. This shift requires interoperable software infrastructure with flexible workflow control.

However, building such a measurement system remains time-consuming for researchers. At the low level, instrument-control implementations must accommodate diverse communication protocols (e.g., TCP/IP, VISA, and serial), which can limit device interchangeability and reuse across systems. At the high level, coordinating workflows that combine conditional logic, iterative processes, and advanced algorithms across multiple libraries frequently leads to redundant implementations, reducing development efficiency. For example, capturing temperature-dependent images with a camera or acquiring temperature-dependent spectra are routine tasks. Although the underlying workflow—iterative parameter adjustment followed by data acquisition—is conceptually identical, such logic is often reimplemented independently across experiments. Moreover, implementing graphical user interfaces (GUIs) for these low- and high-level functionalities typically involves complex multithreading, requiring familiarity with GUI frameworks and operating system (OS) event-handling mechanisms. These challenges impose substantial development overhead and highlight the need for a control framework that balances architectural flexibility with reduced implementation complexity.


# State of the field

Scientific instrument-control software spans general-purpose visual environments and open-source frameworks with different priorities. LabVIEW [@LabVIEW] and MATLAB's Instrument Control Toolbox [@MATLAB] combine instrument communication with workflow and GUI development. QCoDeS [@QCoDeS] and PyMeasure [@PyMeasure] provide instrument abstractions and experimental procedures, while PyOpticon [@PyOpticon] and PyMoDAQ [@PyMoDAQ] emphasize graphical instrument control and data acquisition. Bluesky [@Bluesky] focuses on plan-based orchestration and streaming data management, whereas Atomize [@Atomize] and fsc2 [@fsc2] support script-based experiments through high-level device operations. These systems establish hardware abstraction and reusable measurement logic as common principles, while differing in their emphasis on driver libraries, scripting, graphical interaction, and workflow orchestration.

Within this landscape, the distinguishing focus of `lys_instr` is an explicit three-layer architecture that organizes device abstraction, reusable workflow and GUI logic, and control-system assembly as distinct but connected responsibilities. This organization provides a common route from device-specific communication to reconfigurable interactive applications, allowing instrument implementations to be reused across measurement procedures and system configurations. Its primary use case is custom laboratory automation based on software-coordinated control-and-detect workflows, with hardware-timed procedures incorporated as instrument-level operations where required.


# Software design

The three layers and their relationships are summarized in \autoref{fig:fig1}. Each layer applies established object-oriented design patterns [@Gamma:1994] to define how components are extended, composed, and connected.

![Schematic of the code architecture of `lys_instr`.\label{fig:fig1}](fig1.png)

1. Base Layer: Instrument Abstraction

  This layer defines standardized abstract interfaces for two principal roles in a control-and-detect workflow: *controllers*, which adjust experimental parameters such as external fields, temperature, or physical position, and *detectors*, which acquire data such as images or spectra. Following the *Template Method* pattern, the base interfaces define the device lifecycle, state monitoring, synchronization, and asynchronous execution, while subclasses implement the primitive operations required for device-specific communication. Higher layers interact with different instruments through the same methods, independently of their concrete implementations. Because background monitoring and acquisition are managed by the interfaces, other devices and GUIs can remain responsive, and device-specific subclasses can be integrated directly into higher-level workflows without reimplementing concurrency logic.

2. Top Layer: Workflow Coordination

  This layer constructs hardware-independent workflows from the Base Layer interfaces. In a *scan*, controllers vary experimental parameters while detectors acquire data at each step. Following the *Bridge* pattern, scan execution depends on controller and detector abstractions rather than concrete hardware implementations. The *Composite* pattern allows individual scan processes to be nested into multi-parameter workflows while retaining a common execution model. Prebuilt GUI components invoke the same abstract methods for direct device control and receive state and data updates through event-driven signals, following the *Observer* pattern and avoiding direct dependencies on concrete devices. Consequently, workflow and GUI logic can be reused across different hardware configurations without rebuilding standard control and coordination components.

3. Connection Layer: Control-System Assembly

  This layer assembles components from the Base and Top Layers into an interactive control system, including device interfaces, workflows, data storage, visualization, and GUI components. Following the *Mediator* pattern, it centrally manages connections within and across layers, linking GUI components to their corresponding interfaces and coordinating data flow without direct dependencies among individual components. Concrete hardware details therefore remain confined to the Base Layer, allowing system configurations and GUI layouts to be adapted without application-level implementation of inter-device communication or thread coordination. Prebuilt templates provide starting configurations that can be adapted to individual experimental setups.

Together, these layers allow new instruments to be integrated primarily through device-specific subclasses while reusing asynchronous execution, workflow coordination, and GUI behavior. The predefined abstractions are intended for control-and-detect workflows; experiments organized around substantially different coordination models may require additional components or customized interfaces.


# Example of constructed GUI

With `lys_instr`, users can construct a GUI such as the one shown in \autoref{fig:fig2}. In this example, the `lys_instr` window is embedded in the `lys` platform, with Sector A for data storage, Sector B for detector control, and Sector C for controllers. Multidimensional, nested scan sequences can be defined through the visual interface in the `Scan` tab in Sector C. `lys` tools in the outer window tabs allow on-the-fly customization of the acquired-data visualization.

![Example GUI of `lys_instr`. The main window, embedded in the `lys` window, contains three sectors: Storage panel (A), Detector panel (B), and controller panel (C). The Scan tab in (C) enables dynamic configuration of multi-dimensional, nested experimental workflows.\label{fig:fig2}](fig2.png)


# Research impact statement

`lys_instr` has been deployed in complex scientific experiments and has supported multiple peer-reviewed publications. It has been used to automate ultrafast electron diffraction (UED) and ultrafast transmission electron microscopy (UTEM) systems by coordinating experimental parameters and data acquisition in pump–probe experiments using ultrafast laser excitation and pulsed electron beams [@Nakamura:2020; @Nakamura:2021a; @Nakamura:2022; @Nakamura:2023a; @Shimojima:2021; @Shimojima:2023a; @Shimojima:2023b; @Koga:2024]. It has also been used to control electromagnetic lenses and electron deflectors as part of complex microscopy workflows involving electron-beam precession [@Shiratori:2024; @Hayashi:2025].

The same interface-based workflows have been used to control transmission electron microscopes from multiple manufacturers at RIKEN Center for Emergent Matter Science and Nagoya University, demonstrating portability across hardware configurations. Integration with sister packages in the `lys` family, including `lys_em` [@lys_em] and `lys_fem` [@lys_fem], allows `lys_instr` components to participate in multi-instrument workflows while preserving modularity and extensibility.


# AI usage disclosure

Generative AI tools were used to provide debugging suggestions during the final stages of software development. All code was implemented, reviewed, and verified on real hardware, with functionality confirmed through unit tests and experimental validation.


# Acknowledgements

We acknowledge valuable comments from Takahiro Shimojima and Kyoko Ishizaka. This work was partially supported by Grant-in-Aid for Scientific Research (KAKENHI) Grants No. 21K13889, 	No. 26K17092, and No. 25K00057, and JST PRESTO Grant No. JPMJPR24JA.


# References
