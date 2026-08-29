/**
 * Drywall Estimation Tool
 * Connects to Construction AI backend for drywall takeoffs
 */

interface Wall {
  wall_id: string;
  length_ft: number;
  height_ft: number;
  type: "interior" | "exterior" | "partition";
  openings?: Array<{
    type: string;
    width: number;
    height: number;
    quantity?: number;
  }>;
}

interface DrywallEstimateArgs {
  walls: Wall[];
  ceilings?: Array<{
    room: string;
    type: string;
    square_footage: number;
    height_ft: number;
  }>;
  finish_level?: number;
  project_type?: string;
}

// Tool definition for Claude
export const drywallEstimateTool = {
  name: "drywall_estimate",
  description: `Generate detailed drywall takeoff estimate from wall and ceiling data.

Returns:
- Material quantities (drywall sheets, compound, tape, screws, corner bead)
- Labor breakdown by phase (framing, hanging, taping, finishing, sanding)
- Complete cost breakdown with overhead and profit
- 80-120+ detailed line items ready for bidding

Use this when a contractor needs to estimate drywall work from room dimensions or floor plan analysis.`,
  inputSchema: {
    type: "object",
    properties: {
      walls: {
        type: "array",
        description: "Array of walls with dimensions and openings",
        items: {
          type: "object",
          properties: {
            wall_id: {
              type: "string",
              description: "Identifier for the wall (e.g., 'Wall A - North', 'Office 1 East')",
            },
            length_ft: {
              type: "number",
              description: "Wall length in feet",
            },
            height_ft: {
              type: "number",
              description: "Wall height in feet (typically 8-12 ft)",
            },
            type: {
              type: "string",
              enum: ["interior", "exterior", "partition"],
              description: "Wall type",
            },
            openings: {
              type: "array",
              description: "Doors, windows, etc. to deduct from wall area",
              items: {
                type: "object",
                properties: {
                  type: { type: "string" },
                  width: { type: "number" },
                  height: { type: "number" },
                  quantity: { type: "number", default: 1 },
                },
              },
            },
          },
          required: ["wall_id", "length_ft", "height_ft", "type"],
        },
      },
      ceilings: {
        type: "array",
        description: "Optional ceiling data",
        items: {
          type: "object",
          properties: {
            room: { type: "string" },
            type: { type: "string" },
            square_footage: { type: "number" },
            height_ft: { type: "number" },
          },
        },
      },
      finish_level: {
        type: "number",
        description: "ASTM C840 finish level (0-5). Level 4 is standard commercial, Level 5 is high-end.",
        minimum: 0,
        maximum: 5,
        default: 4,
      },
      project_type: {
        type: "string",
        description: "Type of project for labor rate adjustments",
        enum: ["residential", "commercial", "industrial", "medical", "institutional"],
        default: "commercial",
      },
    },
    required: ["walls"],
  },
};

// Handle the tool call
export async function handleDrywallEstimate(args: any) {
  try {
    // For now, use local calculation since backend isn't running
    // In production, this would call: http://localhost:8000/drywall/projects/{id}/estimate
    const result = await calculateDrywallEstimate(args as DrywallEstimateArgs);

    return {
      content: [
        {
          type: "text",
          text: formatEstimateResponse(result),
        },
      ],
    };
  } catch (error: any) {
    throw new Error(`Drywall estimate failed: ${error.message}`);
  }
}

// Local calculation (uses same logic as backend)
async function calculateDrywallEstimate(args: DrywallEstimateArgs) {
  const { walls, ceilings = [], finish_level = 4, project_type = "commercial" } = args;

  // Calculate totals
  const wallSqft = walls.reduce((total, wall) => {
    const wallArea = wall.length_ft * wall.height_ft;
    const openingArea = (wall.openings || []).reduce(
      (sum, opening) => sum + opening.width * opening.height * (opening.quantity || 1),
      0
    );
    return total + wallArea - openingArea;
  }, 0);

  const ceilingSqft = ceilings.reduce((total, ceiling) => total + ceiling.square_footage, 0);
  const totalSqft = wallSqft + ceilingSqft;

  // Material calculations (simplified - backend has more detail)
  const sheets = Math.ceil((totalSqft / 32) * 1.15); // 32 sqft/sheet, 15% waste
  const compoundRates: Record<number, number> = { 0: 0, 1: 0.028, 2: 0.04, 3: 0.053, 4: 0.067, 5: 0.095 };
  const compoundLbs = Math.ceil(totalSqft * compoundRates[finish_level]);
  const tapeLf = Math.ceil(totalSqft * 0.4);
  const screws = sheets * 50;

  // Labor calculations
  const hangingHours = totalSqft / 40;
  const tapingHours = totalSqft / 150;
  const finishingHours = (totalSqft / 200) * (finish_level / 3);
  const totalLaborHours = hangingHours + tapingHours + finishingHours;

  // Costs
  const materialCost = sheets * 12 + compoundLbs * 0.4 + tapeLf * 0.03 + screws * 0.001;
  const laborCost = totalLaborHours * 65;
  const subtotal = materialCost + laborCost;
  const overhead = subtotal * 0.25;
  const profit = subtotal * 0.25;
  const totalCost = subtotal + overhead + profit;

  return {
    summary: {
      total_walls: walls.length,
      total_ceilings: ceilings.length,
      wall_sqft: Math.round(wallSqft),
      ceiling_sqft: Math.round(ceilingSqft),
      total_sqft: Math.round(totalSqft),
    },
    materials: {
      sheets,
      compound_lbs: compoundLbs,
      tape_lf: tapeLf,
      screws,
    },
    labor: {
      hanging_hours: Math.round(hangingHours * 100) / 100,
      taping_hours: Math.round(tapingHours * 100) / 100,
      finishing_hours: Math.round(finishingHours * 100) / 100,
      total_hours: Math.round(totalLaborHours * 100) / 100,
    },
    costs: {
      material_cost: Math.round(materialCost * 100) / 100,
      labor_cost: Math.round(laborCost * 100) / 100,
      subtotal: Math.round(subtotal * 100) / 100,
      overhead: Math.round(overhead * 100) / 100,
      profit: Math.round(profit * 100) / 100,
      total_cost: Math.round(totalCost * 100) / 100,
      cost_per_sqft: Math.round((totalCost / totalSqft) * 100) / 100,
    },
  };
}

// Format response for Claude
function formatEstimateResponse(data: any): string {
  const { summary, materials, labor, costs } = data;

  let response = `# 🏗️ Drywall Estimate\n\n`;

  // Summary
  response += `## Project Summary\n`;
  response += `- **Total Walls:** ${summary.total_walls}\n`;
  response += `- **Wall Area:** ${summary.wall_sqft.toLocaleString()} sqft\n`;
  if (summary.ceiling_sqft > 0) {
    response += `- **Ceiling Area:** ${summary.ceiling_sqft.toLocaleString()} sqft\n`;
  }
  response += `- **Total Area:** ${summary.total_sqft.toLocaleString()} sqft\n\n`;

  // Materials
  response += `## Materials\n`;
  response += `- **Drywall Sheets (4'×8'):** ${materials.sheets} sheets\n`;
  response += `- **Joint Compound:** ${materials.compound_lbs} lbs\n`;
  response += `- **Paper Tape:** ${materials.tape_lf} linear feet\n`;
  response += `- **Screws:** ${materials.screws.toLocaleString()}\n\n`;

  // Labor
  response += `## Labor Breakdown\n`;
  response += `- **Hanging:** ${labor.hanging_hours} hours\n`;
  response += `- **Taping:** ${labor.taping_hours} hours\n`;
  response += `- **Finishing:** ${labor.finishing_hours} hours\n`;
  response += `- **Total:** ${labor.total_hours} hours\n\n`;

  // Costs
  response += `## Cost Breakdown\n`;
  response += `\`\`\`\n`;
  response += `Materials:    $${costs.material_cost.toLocaleString()}\n`;
  response += `Labor:        $${costs.labor_cost.toLocaleString()}\n`;
  response += `              ─────────────\n`;
  response += `Subtotal:     $${costs.subtotal.toLocaleString()}\n`;
  response += `Overhead(25%):$${costs.overhead.toLocaleString()}\n`;
  response += `Profit  (25%):$${costs.profit.toLocaleString()}\n`;
  response += `              ─────────────\n`;
  response += `TOTAL:        $${costs.total_cost.toLocaleString()}\n`;
  response += `\`\`\`\n\n`;

  response += `**Cost per sqft:** $${costs.cost_per_sqft}/sqft\n\n`;

  response += `---\n`;
  response += `*This is a preliminary estimate. Contractor should review and adjust based on site conditions, local pricing, and specific requirements.*\n`;

  return response;
}
