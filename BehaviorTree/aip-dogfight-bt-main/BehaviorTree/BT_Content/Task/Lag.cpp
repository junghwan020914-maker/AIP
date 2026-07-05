#include "Lag.h"

namespace Action
{
	PortsList Lag::providedPorts()
	{
		return {
			InputPort<CPPBlackBoard*>("BB"),
			// 적기 후미에서 겨냥할 거리(m). 0이면 거리의 절반을 자동 사용
			InputPort<double>("LagDistance", 0.0, "lag point distance behind target in meters (0 = auto)")
		};
	}

	NodeStatus Lag::tick()
	{
		Optional<CPPBlackBoard*> BB = getInput<CPPBlackBoard*>("BB");
		double LagDistance = getInput<double>("LagDistance").value();

		Vector3 TargetLocation = (*BB)->TargetLocaion_Cartesian;	// 적기 현재 위치
		Vector3 TFV = (*BB)->TargetForwardVector;					// 적기 진행 방향
		TFV.normalize();											// 단위 벡터화(안전)

		float Distance = (*BB)->Distance;							// 적기와의 거리 (m)

		// 자동 모드(0 이하)면 거리의 절반을 후미 겨냥 거리로 사용
		double Lag = (LagDistance <= 0.0) ? (double)Distance * 0.5 : LagDistance;

		// 적기 진행 방향의 반대쪽(꼬리 뒤)을 겨냥
		Vector3 LagPoint = TargetLocation - TFV * Lag;

		(*BB)->VP_Cartesian = LagPoint;

		return NodeStatus::SUCCESS;
	}
}
