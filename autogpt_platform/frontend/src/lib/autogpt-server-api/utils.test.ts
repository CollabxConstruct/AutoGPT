import { describe, test, expect } from "vitest";
import { formatEdgeID } from "./utils";
import { Link } from "./types";
import { Connection } from "@xyflow/react";

describe("formatEdgeID", () => {
  test("test_formatEdgeID_with_link", () => {
    const link: Link = {
      id: "link-1",
      source_id: "src-node",
      source_name: "output_1",
      sink_id: "sink-node",
      sink_name: "input_1",
      is_static: false,
    };

    const result = formatEdgeID(link);
    expect(result).toBe("src-node_output_1_sink-node_input_1");
  });

  test("test_formatEdgeID_with_connection", () => {
    const connection: Connection = {
      source: "source-node-id",
      sourceHandle: "output_handle",
      target: "target-node-id",
      targetHandle: "input_handle",
    };

    const result = formatEdgeID(connection);
    expect(result).toBe(
      "source-node-id_output_handle_target-node-id_input_handle",
    );
  });
});
