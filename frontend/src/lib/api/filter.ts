import { apiClient } from "@/lib/api";
import type {
  AdvancedFilterPayload,
  AdvancedFilterResponse,
  FilterableField,
} from "@/types/filter";

export async function fetchAdvancedFilter(
  payload: AdvancedFilterPayload,
): Promise<AdvancedFilterResponse> {
  const { data } = await apiClient.post<AdvancedFilterResponse>(
    "/api/v1/filter/advanced",
    payload,
  );
  return data;
}

export async function fetchFilterableFields(): Promise<FilterableField[]> {
  const { data } = await apiClient.get<{ status: string; fields: FilterableField[] }>(
    "/api/v1/filter/fields",
  );
  return data.fields;
}
