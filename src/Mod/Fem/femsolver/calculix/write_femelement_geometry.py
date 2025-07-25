# ***************************************************************************
# *   Copyright (c) 2021 Bernd Hahnebach <bernd@bimstatik.org>              *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

__title__ = "FreeCAD FEM calculix write inpfile femelement geometry"
__author__ = "Bernd Hahnebach"
__url__ = "https://www.freecad.org"


def write_femelement_geometry(f, ccxwriter):

    # floats read from ccx should use {:.13G}, see comment in writer module

    f.write("\n{}\n".format(59 * "*"))
    f.write("** Sections\n")
    for matgeoset in ccxwriter.mat_geo_sets:
        if matgeoset["ccx_elset"]:
            elsetdef = "ELSET={}, ".format(matgeoset["ccx_elset_name"])
            material = "MATERIAL={}".format(matgeoset["mat_obj_name"])

            if "beamsection_obj" in matgeoset:  # beam mesh
                beamsec_obj = matgeoset["beamsection_obj"]
                beam_axis_m = matgeoset["beam_axis_m"]
                # in CalxuliX called the 1direction
                # see meshtools.get_beam_main_axis_m(beam_direction, defined_angle)
                section_nor = "{:.13G}, {:.13G}, {:.13G}\n".format(
                    beam_axis_m[0], beam_axis_m[1], beam_axis_m[2]
                )
                if beamsec_obj.SectionType == "Rectangular":
                    # see meshtools.get_beam_main_axis_m(beam_direction, defined_angle)
                    # the method get_beam_main_axis_m() which calculates the beam_axis_m vector
                    # unless rotated, this vector points towards +y axis
                    # doesn't follow 1,2-direction order of CalculiX
                    # ^ (n, 2-direction)
                    # |
                    # |
                    # .----> (m, 1-direction)
                    #
                    len_beam_axis_n = beamsec_obj.RectHeight.getValueAs("mm").Value
                    len_beam_axis_m = beamsec_obj.RectWidth.getValueAs("mm").Value
                    section_type = ", SECTION=RECT"
                    section_geo = f"{len_beam_axis_m:.13G},{len_beam_axis_n:.13G}\n"
                    section_def = f"*BEAM SECTION, {elsetdef}{material}{section_type}\n"
                elif beamsec_obj.SectionType == "Circular":
                    diameter = beamsec_obj.CircDiameter.getValueAs("mm").Value
                    section_type = ", SECTION=CIRC"
                    section_geo = f"{diameter:.13G}\n"
                    section_def = f"*BEAM SECTION, {elsetdef}{material}{section_type}\n"
                elif beamsec_obj.SectionType == "Elliptical":
                    axis1 = beamsec_obj.Axis1Length.getValueAs("mm").Value
                    axis2 = beamsec_obj.Axis2Length.getValueAs("mm").Value
                    section_type = ", SECTION=CIRC"
                    section_geo = f"{axis1:.13G},{axis2:.13G}\n"
                    section_def = f"*BEAM SECTION, {elsetdef}{material}{section_type}\n"
                elif beamsec_obj.SectionType == "Pipe":
                    radius = 0.5 * beamsec_obj.PipeDiameter.getValueAs("mm").Value
                    thickness = beamsec_obj.PipeThickness.getValueAs("mm").Value
                    section_type = ", SECTION=PIPE"
                    section_geo = f"{radius:.13G},{thickness:.13G}\n"
                    section_def = f"*BEAM SECTION, {elsetdef}{material}{section_type}\n"
                elif beamsec_obj.SectionType == "Box":
                    box_width = beamsec_obj.BoxWidth.getValueAs("mm").Value
                    box_height = beamsec_obj.BoxHeight.getValueAs("mm").Value
                    box_t1 = beamsec_obj.BoxT1.getValueAs("mm").Value
                    box_t2 = beamsec_obj.BoxT2.getValueAs("mm").Value
                    box_t3 = beamsec_obj.BoxT3.getValueAs("mm").Value
                    box_t4 = beamsec_obj.BoxT4.getValueAs("mm").Value
                    section_type = ", SECTION=BOX"
                    section_geo = f"{box_width:.13G},{box_height:.13G},{box_t1:.13G},{box_t2:.13G},{box_t3:.13G},{box_t4:.13G}\n"
                    section_def = f"*BEAM SECTION, {elsetdef}{material}{section_type}\n"

                f.write(section_def)
                f.write(section_geo)
                f.write(section_nor)
            elif "fluidsection_obj" in matgeoset:  # fluid mesh
                fluidsec_obj = matgeoset["fluidsection_obj"]
                if fluidsec_obj.SectionType == "Liquid":
                    section_type = fluidsec_obj.LiquidSectionType
                    if (section_type == "PIPE INLET") or (section_type == "PIPE OUTLET"):
                        section_type = "PIPE INOUT"
                    section_def = "*FLUID SECTION, {}TYPE={}, {}\n".format(
                        elsetdef, section_type, material
                    )
                    section_geo = liquid_section_def(fluidsec_obj, section_type)
                """
                # deactivate as it would result in section_def and section_geo not defined
                # deactivated in the App and Gui object and thus in the task panel as well
                elif fluidsec_obj.SectionType == "Gas":
                    section_type = fluidsec_obj.GasSectionType
                elif fluidsec_obj.SectionType == "Open Channel":
                    section_type = fluidsec_obj.ChannelSectionType
                """
                f.write(section_def)
                f.write(section_geo)
            elif "shellthickness_obj" in matgeoset:  # shell mesh
                shellth_obj = matgeoset["shellthickness_obj"]
                if ccxwriter.solver_obj.ModelSpace == "3D":
                    offset = shellth_obj.Offset
                    section_def = f"*SHELL SECTION, {elsetdef}{material}, OFFSET={offset:.13G}\n"
                else:
                    section_def = f"*SOLID SECTION, {elsetdef}{material}\n"
                thickness = shellth_obj.Thickness.getValueAs("mm").Value
                section_geo = f"{thickness:.13G}\n"
                f.write(section_def)
                f.write(section_geo)
            else:  # solid mesh
                section_def = f"*SOLID SECTION, {elsetdef}{material}\n"
                f.write(section_def)


# ************************************************************************************************
# Helpers
def liquid_section_def(obj, section_type):
    if section_type == "PIPE MANNING":
        manning_area = obj.ManningArea.getValueAs("mm^2").Value
        manning_radius = obj.ManningRadius.getValueAs("mm").Value
        manning_coefficient = obj.ManningCoefficient
        section_geo = "{:.13G},{:.13G},{:.13G}\n".format(
            manning_area, manning_radius, manning_coefficient
        )
        return section_geo
    elif section_type == "PIPE ENLARGEMENT":
        enlarge_area1 = obj.EnlargeArea1.getValueAs("mm^2").Value
        enlarge_area2 = obj.EnlargeArea2.getValueAs("mm^2").Value
        section_geo = f"{enlarge_area1:.13G},{enlarge_area2:.13G}\n"
        return section_geo
    elif section_type == "PIPE CONTRACTION":
        contract_area1 = obj.ContractArea1.getValueAs("mm^2").Value
        contract_area2 = obj.ContractArea2.getValueAs("mm^2").Value
        section_geo = f"{contract_area1:.13G},{contract_area2:.13G}\n"
        return section_geo
    elif section_type == "PIPE ENTRANCE":
        entrance_pipe_area = obj.EntrancePipeArea.getValueAs("mm^2").Value
        entrance_area = obj.EntranceArea.getValueAs("mm^2").Value
        section_geo = f"{entrance_pipe_area:.13G},{entrance_area:.13G}\n"
        return section_geo
    elif section_type == "PIPE DIAPHRAGM":
        diaphragm_pipe_area = obj.DiaphragmPipeArea.getValueAs("mm^2").Value
        diaphragm_area = obj.DiaphragmArea.getValueAs("mm^2").Value
        section_geo = f"{diaphragm_pipe_area:.13G},{diaphragm_area:.13G}\n"
        return section_geo
    elif section_type == "PIPE BEND":
        bend_pipe_area = obj.BendPipeArea.getValueAs("mm^2").Value
        bend_radius_diameter = obj.BendRadiusDiameter
        bend_angle = obj.BendAngle
        bend_loss_coefficient = obj.BendLossCoefficient
        section_geo = "{:.13G},{:.13G},{:.13G},{:.13G}\n".format(
            bend_pipe_area, bend_radius_diameter, bend_angle, bend_loss_coefficient
        )
        return section_geo
    elif section_type == "PIPE GATE VALVE":
        gatevalve_pipe_area = obj.GateValvePipeArea.getValueAs("mm^2").Value
        gatevalve_closing_coeff = obj.GateValveClosingCoeff
        section_geo = f"{gatevalve_pipe_area:.13G},{gatevalve_closing_coeff:.13G}\n"
        return section_geo
    elif section_type == "PIPE WHITE-COLEBROOK":
        colebrooke_area = obj.ColebrookeArea.getValueAs("mm^2").Value
        colebrooke_diameter = 2 * obj.ColebrookeRadius.getValueAs("mm")
        colebrooke_grain_diameter = obj.ColebrookeGrainDiameter.getValueAs("mm")
        colebrooke_form_factor = obj.ColebrookeFormFactor
        section_geo = "{:.13G},{:.13G},{},{:.13G},{:.13G}\n".format(
            colebrooke_area,
            colebrooke_diameter,
            "-1",
            colebrooke_grain_diameter,
            colebrooke_form_factor,
        )
        return section_geo
    elif section_type == "LIQUID PUMP":
        section_geo = ""
        for i in range(len(obj.PumpFlowRate)):
            flow_rate = obj.PumpFlowRate[i]
            top = obj.PumpHeadLoss[i]
            section_geo = f"{section_geo + flow_rate:.13G},{top:.13G},\n"
        section_geo = f"{section_geo}\n"
        return section_geo
    else:
        return ""
